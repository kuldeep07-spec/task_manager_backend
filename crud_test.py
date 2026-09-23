# Tests create_user() from crud.py by actually inserting a real row
# into MySQL and printing back its auto-generated id.
# NOTE: running this more than once will fail on the 2nd run, since
# the email would already exist (UNIQUE constraint) — that's expected.

from database import SessionLocal      # session factory, built in database.py
from crud import create_user           # the function we're testing

db = SessionLocal()                    # open a real session/connection

new_user = create_user(db, name="Test Python User01", email="testpython01@example.com")

print("Created user with id:", new_user.id)  # proves the row was saved (id only exists after commit)

db.close()                              # always close the session when done