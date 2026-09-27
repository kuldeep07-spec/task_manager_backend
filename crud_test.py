# crud_test.py
# Manual test script for the functions in crud.py.
# Runs through all 5 CRUD operations in sequence, using real data
# from the MySQL database, to confirm each function works correctly.
#
# ⚠️ CAUTION: this file both creates AND deletes real data every run.
# Re-running it repeatedly will keep adding "Test Python User0N" rows
# (change the email each time) and will keep deleting user id 5 —
# after the first run, id 5 no longer exists, so Tests 3-5 will fail
# with "None has no attribute name" once that happens.

from database import SessionLocal
from crud import create_user, get_all, get_user_by_id, update_user_email, delete_user

db = SessionLocal()  # open a real session/connection


# --- Test 1: Create a new user ---
# Equivalent SQL: INSERT INTO users (name, email) VALUES (...);
# NOTE: change the email before each re-run, or this fails with
# IntegrityError (1062, Duplicate entry) since email is UNIQUE.
new_user = create_user(db, name="Test Python User01", email="testpython01@example.com")
print("Created user with id:", new_user.id)


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


# --- Test 4: Update that user's email ---
# Equivalent SQL: UPDATE users SET email = 'helloworld@gmail.com' WHERE id = 5;
update_in_user = update_user_email(db, 5, "helloworld@gmail.com")
print("updated_email:", update_in_user.email)


# --- Test 5: Delete that same user ---
# Equivalent SQL: DELETE FROM users WHERE id = 5;
# NOTE: this also cascades — deletes all of user 5's tasks too,
# thanks to ON DELETE CASCADE on the task table's foreign key.
del_user = delete_user(db, 5)
print("deleted_user:", del_user.id, del_user.name, del_user.email)


db.close()  # always close the session when done