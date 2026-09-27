from sqlalchemy.orm import Session   # type hint for the db session parameter
from models import User               # the User model, defined in models.py


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
# READ — all rows
# ─────────────────────────────────────────────
# Fetches every user in the table.
# Equivalent SQL: SELECT * FROM users;
def get_all(db: Session):
    return db.query(User).all()
    # db.query(User)  -> "I want rows from the users table"
    # .all()          -> "give me every matching row, as a list" (no filter = no conditions)


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
# NOTE: because task.user_id has ON DELETE CASCADE in MySQL, deleting a
# user here will also automatically delete all of their tasks.
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