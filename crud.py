from sqlalchemy.orm import Session   # type hint for the db session parameter
from models import User, Task        # the models defined in models.py


# ─────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────
# Creates a new user row in the database.
# Equivalent SQL: INSERT INTO users (name, email) VALUES (...);
def create_user(db: Session, name: str, email: str):
    new_user = User(name=name, email=email)
    # ↑ Step 1: build the row as a Python object, in memory only.
    #   Nothing has touched MySQL yet. new_user.id is still empty here,
    #   since MySQL hasn't generated it — AUTO_INCREMENT only happens on insert.

    db.add(new_user)
    # ↑ Step 2: stage the change in this session.
    #   Like typing the INSERT statement but not running it yet.

    db.commit()
    # ↑ Step 3: actually save it to MySQL — same idea as SQL's COMMIT.
    #   This is the moment the row genuinely becomes permanent in the database.

    db.refresh(new_user)
    # ↑ Step 4: reload new_user from the database.
    #   Needed because MySQL generated the real id during commit, but our
    #   Python object doesn't automatically know that — refresh() catches it up.

    return new_user   # hand back the saved row, now with its real id filled in


# ─────────────────────────────────────────────
# READ — users, one page at a time
# ─────────────────────────────────────────────
# Fetches one page of users, sorted by id.
# Equivalent SQL: SELECT * FROM users ORDER BY id LIMIT <limit> OFFSET <skip>;
# skip  = how many rows to skip first (OFFSET). Formula: (page - 1) * page_size
# limit = how many rows to return (LIMIT, the page size)
# Defaults (0 and 10) apply when the caller sends nothing, so /users never
# returns the whole table at once.
def get_all(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()
    # order_by -> fixed sort order, so pages never overlap or skip rows
    # offset   -> skip the first `skip` rows
    # limit    -> return at most `limit` rows
    # .all()   -> run the query and return the rows as a list


# ─────────────────────────────────────────────
# READ — tasks, with optional filter and pagination
# ─────────────────────────────────────────────
# Fetches one page of tasks, optionally only done or only not-done ones.
# Equivalent SQL: SELECT * FROM tasks [WHERE is_done = ...]
#                 ORDER BY id LIMIT <limit> OFFSET <skip>;
# is_done = True  -> only done tasks
#           False -> only unfinished tasks
#           None  -> no filter, all tasks (the default)
def get_tasks(db: Session, is_done: bool | None = None, skip: int = 0, limit: int = 10):
    query = db.query(Task)
    # ↑ Build the query but don't run it yet. It's still just a plan,
    #   so we can keep adding to it.

    if is_done is not None:
        # ↑ "is not None", not "if is_done:". When the caller sends False,
        #   `if is_done:` would be falsy and skip the filter by mistake.
        query = query.filter(Task.is_done == is_done)
        # ↑ Add to the SAME query. Don't restart from db.query(Task),
        #   or the query built above gets thrown away.

    return query.order_by(Task.id).offset(skip).limit(limit).all()
    # ↑ The filter runs first, then the page is taken from the filtered rows.
    #   .all() is the moment the query actually runs.


# ─────────────────────────────────────────────
# READ — one row by id
# ─────────────────────────────────────────────
# Fetches a single user, matched by their id.
# Equivalent SQL: SELECT * FROM users WHERE id = <user_id>;
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
    # db.query(User)               -> "I want rows from the users table"
    # .filter(User.id == user_id)  -> "...but only where id matches" (note: == not =)
    # .first()                     -> "give me just the first match (or None if none found)"


# Fetches a single task, matched by the TASK's own id (not the owner's id).
# Equivalent SQL: SELECT * FROM tasks WHERE id = <task_id>;
# Returns None if no task has that id.
def get_task_by_id(db: Session, task_id: int):
    return db.query(Task).filter(Task.id == task_id).first()


# ─────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────
# Changes an existing user's email.
# Equivalent SQL: UPDATE users SET email = <new_email> WHERE id = <user_id>;
def update_user_email(db: Session, user_id: int, new_email: str):
    user = db.query(User).filter(User.id == user_id).first()
    # ↑ Step 1: fetch the row first — SQLAlchemy needs the actual object
    #   in hand before it can track and apply a change to it.

    if user:
        # ↑ Guard against user_id not matching any row (user would be None).
        #   Without this check, user.email = ... on None would crash.

        user.email = new_email
        # ↑ Step 2: just change the attribute directly, like any normal
        #   Python variable. SQLAlchemy quietly tracks that this changed.

        db.commit()
        # ↑ Step 3: save the change to MySQL. Only the changed column
        #   (email) gets sent in the actual UPDATE statement — name/id
        #   are untouched.

        db.refresh(user)
        # ↑ Reload from DB to make sure our Python object matches
        #   exactly what's now stored (good habit, mirrors create_user).

    return user   # returns the updated user, or None if no match was found


# ─────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────
# Removes a user row entirely.
# Equivalent SQL: DELETE FROM users WHERE id = <user_id>;
# ⚠️ KNOWN ISSUE: the MySQL foreign key has ON DELETE CASCADE, but because
# User has a tasks relationship(), SQLAlchemy first sets each task's user_id
# to NULL, so the cascade never fires. The user's tasks are left behind as
# orphans (user_id = NULL). Fix: passive_deletes=True on User.tasks in
# models.py. Update this comment once that's applied and tested.
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    # ↑ Step 1: fetch the row first, same reasoning as update — need the
    #   actual object in hand to tell SQLAlchemy what to delete.

    if user:
        # ↑ Guard against user_id not matching any row.

        db.delete(user)
        # ↑ Step 2: mark this row for deletion (staged, not yet permanent).

        db.commit()
        # ↑ Step 3: actually remove it from MySQL. This is the point of
        #   no return — same COMMIT concept as everywhere else.

    return user   # returns the (now-deleted) user object, or None if no match