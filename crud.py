from sqlalchemy.orm import Session   # type hint for the db session parameter
from models import User, Task        # the models defined in models.py
from sqlalchemy.exc import IntegrityError   # raised when the database refuses a row
                                            # (e.g. duplicate email -> UNIQUE violated)

# ═════════════════════════════════════════════════════════════════════════
# crud.py : REVISION GUIDE (read this first)
# ═════════════════════════════════════════════════════════════════════════
# JOB OF THIS FILE
#   Database functions only: create, read, update, delete (CRUD).
#   Think of it as "the librarian": it looks things up and changes them.
#   It knows NOTHING about HTTP. No status codes, no HTTPException here.
#   The route in main.py ("the front desk") turns results into 404 / 409.
#
# THE FLOW OF ONE REQUEST
#   client -> main.py route -> crud.py function -> models.py -> database.py
#          -> PostgreSQL
#
# THE `db` PARAMETER
#   Every function receives `db`, a Session. It comes from get_db() in
#   database.py through Depends(get_db) in the route. One session per
#   request, closed automatically afterwards. A session = one transaction.
#
# THE FOUR VERBS (SQLAlchemy <-> SQL)
#   db.query(Model).filter(...)   ->  SELECT ... WHERE ...
#   db.add(obj) + db.commit()     ->  INSERT + COMMIT
#   obj.field = value + commit()  ->  UPDATE + COMMIT
#   db.delete(obj) + commit()     ->  DELETE + COMMIT
#
# WHAT EACH FUNCTION RETURNS (the contract with main.py)
#   create_user     -> the new User, or None if the email already exists
#   get_all/get_tasks -> a list (an empty list [] is a valid answer)
#   get_*_by_id     -> one object, or None if not found
#   update_*        -> the updated object, or None if not found
#   delete_task     -> True if deleted, False if not found
#   The route checks for None / False and raises 404 (or 409 for create).
#
# QUICK REVISION METHOD
#   Cover the code, rewrite one function from a blank file, then compare.
#   Order for revising: get_task_by_id -> get_tasks -> update -> delete -> create.
# ═════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────
# Creates a new user row in the database.
# Equivalent SQL: INSERT INTO users (name, email) VALUES (...) RETURNING id;
# Returns: the saved User (with its real id), or None if the email is taken.
#
# EDGE CASE: duplicate email.
#   The users.email column is UNIQUE. PostgreSQL refuses the second insert,
#   SQLAlchemy raises IntegrityError at db.commit(). We catch it here, undo
#   with rollback, and return None. main.py then raises 409 "Email already
#   exists". Without this, the client would see a 500 server error.
# TRADEOFF (for the README):
#   Naive version: check "does this email exist?" first, then insert.
#   Constraint: two requests with the same email can arrive at the same
#   moment and both pass the check. The database UNIQUE rule is the final
#   guard, so we let it decide and catch its error. Cost: a failed insert
#   still uses up an id number (gaps in ids are normal and harmless).
def create_user(db: Session, name: str, email: str):
    new_user = User(name=name, email=email)
    # ↑ Step 1: build the row as a Python object, in memory only.
    #   Nothing has touched PostgreSQL yet. new_user.id is still empty,
    #   because PostgreSQL generates the id (identity column) on insert.

    db.add(new_user)
    # ↑ Step 2: stage the change in this session.
    #   Like typing the INSERT statement but not running it yet.

    try:
        db.commit()
        # ↑ Step 3: actually save to PostgreSQL (SQL's COMMIT). This is the
        #   moment the INSERT really runs, so this is the line that can fail.
    except IntegrityError:
        db.rollback()
        # ↑ Cancel the failed attempt. This cleans the session so it is not
        #   left in a broken state after the error.
        return None
        # ↑ None tells the caller "it did not work" (duplicate email).

    db.refresh(new_user)
    # ↑ Step 4: reload new_user from the database.
    #   PostgreSQL generated the real id during commit, but our Python
    #   object does not know it yet. refresh() catches it up.
    #   It only runs if the commit succeeded (the except branch returned).

    return new_user   # hand back the saved row, now with its real id filled in


# ─────────────────────────────────────────────
# READ: users, one page at a time
# ─────────────────────────────────────────────
# Fetches one page of users, sorted by id.
# Equivalent SQL: SELECT * FROM users ORDER BY id LIMIT <limit> OFFSET <skip>;
# skip  = how many rows to skip first (OFFSET). Formula: (page - 1) * page_size
# limit = how many rows to return (LIMIT, the page size)
# Defaults (0 and 10) apply when the caller sends nothing, so /users never
# returns the whole table at once.
# Returns: a list (empty list [] if there are no users on that page).
def get_all(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()
    # order_by -> fixed sort order, so pages never overlap or skip rows.
    #             PostgreSQL does NOT guarantee any order without ORDER BY
    #             (an UPDATE can even move a row's position).
    # offset   -> skip the first `skip` rows
    # limit    -> return at most `limit` rows
    # .all()   -> run the query and return the rows as a list


# ─────────────────────────────────────────────
# READ: tasks, with optional filter and pagination
# ─────────────────────────────────────────────
# Fetches one page of tasks, optionally only done or only not-done ones.
# Equivalent SQL: SELECT * FROM tasks [WHERE is_done = ...]
#                 ORDER BY id LIMIT <limit> OFFSET <skip>;
# is_done = True  -> only done tasks
#           False -> only unfinished tasks
#           None  -> no filter, all tasks (the default)
# Called from main.py with query parameters: /tasks?is_done=false&skip=0&limit=10
def get_tasks(db: Session, is_done: bool | None = None, skip: int = 0, limit: int = 10):
    query = db.query(Task)
    # ↑ Build the query but don't run it yet. It's still just a plan,
    #   so we can keep adding to it.

    if is_done is not None:
        # ↑ "is not None", not "if is_done:". When the caller sends False,
        #   `if is_done:` would be falsy and skip the filter by mistake.
        query = query.filter(Task.is_done == is_done)
        # ↑ filter = SQL's WHERE. Use == (comparison), never = (assignment),
        #   and name the column: Task.is_done, not just is_done.
        #   Add to the SAME query. Don't restart from db.query(Task),
        #   or the query built above gets thrown away.

    return query.order_by(Task.id).offset(skip).limit(limit).all()
    # ↑ The filter runs first, then the page is taken from the filtered rows.
    #   .all() is the moment the query actually runs.
    #   offset (not "skip"!) is the SQLAlchemy name for OFFSET.


# ─────────────────────────────────────────────
# READ: one row by id
# ─────────────────────────────────────────────
# Fetches a single user, matched by their id.
# Equivalent SQL: SELECT * FROM users WHERE id = <user_id>;
# Returns: the User, or None if there is no such user.
# main.py uses the None to raise 404 "User not found".
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
    # db.query(User)               -> "I want rows from the users table"
    # .filter(User.id == user_id)  -> "...but only where id matches" (note: == not =)
    # .first()                     -> "give me just the first match (or None if none found)"
    #                                 (.all() would give a LIST, [] when nothing matches)


# Fetches a single task, matched by the TASK's own id (not the owner's id).
# Equivalent SQL: SELECT * FROM tasks WHERE id = <task_id>;
# Returns None if no task has that id.
# Same shape as get_user_by_id. Revise this one first: it is the simplest pattern.
def get_task_by_id(db: Session, task_id: int):
    return db.query(Task).filter(Task.id == task_id).first()


# ─────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────
# Changes an existing user's email.
# Equivalent SQL: UPDATE users SET email = <new_email> WHERE id = <user_id>;
# Returns: the updated User, or None if there is no such user.
#
# KNOWN GAP (to fix later, same fix as create_user):
#   If new_email already belongs to ANOTHER user, db.commit() raises
#   IntegrityError and the client sees a 500. To fix: wrap commit in
#   try/except IntegrityError, call db.rollback(), return None, and let the
#   route raise 409. (Right now None here also means "user not found", so
#   the route would need a way to tell the two cases apart.)
# TRADEOFF: this does a SELECT first, then an UPDATE (two queries). That is
#   simple and gives a clean 404. A single UPDATE ... RETURNING * would be
#   one query, but it does not fit the ORM style used here.
def update_user_email(db: Session, user_id: int, new_email: str):
    user = db.query(User).filter(User.id == user_id).first()
    # ↑ Step 1: fetch the row first. SQLAlchemy needs the actual object
    #   in hand before it can track and apply a change to it.

    if user:
        # ↑ Guard against user_id not matching any row (user would be None).
        #   Without this check, user.email = ... on None would crash.
        #   `if user:` is fine here: a real User object is always truthy.

        user.email = new_email
        # ↑ Step 2: just change the attribute directly, like any normal
        #   Python variable. SQLAlchemy quietly tracks that this changed.

        db.commit()
        # ↑ Step 3: save the change to PostgreSQL. Only the changed column
        #   (email) gets sent in the actual UPDATE statement. name and id
        #   are untouched. Forget this line and the change silently vanishes
        #   when the session closes.

        db.refresh(user)
        # ↑ Reload from DB to make sure our Python object matches
        #   exactly what is now stored (good habit, mirrors create_user).

    return user   # returns the updated user, or None if no match was found


# ─────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────
# Removes a task row entirely.
# Equivalent SQL: DELETE FROM tasks WHERE id = <task_id>;
# Returns: True if a task was deleted, False if no task had that id.
# main.py turns False into a 404 "Task not found".
#
# WHY True/False and not the task object?
#   After db.commit(), a deleted object is detached from the session.
#   Returning it and using it later can raise DetachedInstanceError.
#   A plain True/False is all the route needs.
#
# RELATED NOTE (when you add a delete_user function later):
#   The foreign key tasks.user_id has ON DELETE CASCADE in the database,
#   so deleting a user deletes their tasks. The User.tasks relationship in
#   models.py uses passive_deletes=True so SQLAlchemy leaves that cleanup
#   to the database. Without it, SQLAlchemy first sets each task's user_id
#   to NULL, the cascade has nothing left to delete, and orphan tasks stay.
def delete_task(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()
    # ↑ Look the row up first. .first() gives the Task, or None if missing.

    if task is None:
        return False
        # ↑ Nothing to delete. Stop here, change nothing, report "not found".

    db.delete(task)
    # ↑ Mark the object for deletion (SQL DELETE, not run yet).

    db.commit()
    # ↑ Run the DELETE and save it. Forget this and nothing is deleted.

    return True   # True = a task was found and deleted