# crud_test.py
# Manual test script for the functions in crud.py.
# Runs Create, Read-all, and Read-by-id in sequence to confirm each works
# against the real MySQL database.

from database import SessionLocal              # session factory, built in database.py
from crud import create_user, get_all, get_user_by_id   # functions being tested

db = SessionLocal()                             # open a real session/connection


# --- Test 1: Create a new user ---
# Equivalent SQL: INSERT INTO users (name, email) VALUES (...);
# NOTE: change the email before each re-run, or this will fail with
# IntegrityError (1062, Duplicate entry) since email is UNIQUE.
new_user = create_user(db, name="Test Python User01", email="testpython01@example.com")
print("Created user with id:", new_user.id)     # id only exists after commit + refresh


# --- Test 2: Get all users ---
# Equivalent SQL: SELECT * FROM users;
all_users = get_all(db)
print("all users", len(all_users))
for user in all_users:
    print(user.id, user.name, user.email)


# --- Test 3: Get one user by id ---
# Equivalent SQL: SELECT * FROM users WHERE id = 5;
search_by_user = get_user_by_id(db, 5)
print("userdetail", search_by_user.name, search_by_user.email)


db.close()                                       # always close the session when done