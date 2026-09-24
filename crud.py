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