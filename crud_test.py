# crud_test.py
# Manual test script for the functions in crud.py.
# Runs create, read (users and tasks), update and delete against the real
# MySQL database, to confirm each function works.
#
# ⚠️ CAUTION: this file changes real data every run (creates and deletes users).
# It is NOT safe to re-run as-is. See the warning above each test.

from database import SessionLocal
from crud import (
    create_user, get_all, get_user_by_id, update_user_email,
    delete_user, get_task_by_id, get_tasks,
)

db = SessionLocal()  # open a real session/connection


# --- Test 1: Create a new user ---
# Equivalent SQL: INSERT INTO users (name, email) VALUES (...);
# ⚠️ Email is UNIQUE, so the 2nd run fails with IntegrityError (1062).
#    Change the email before each re-run, or comment this test out.
new_user = create_user(db, name="Test Python User01", email="testpython01@example.com")
print("Created user with id:", new_user.id)


# --- Test 2: Get one page of users ---
# Equivalent SQL: SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 0;
# get_all now paginates, so this returns at most 10 users (the default
# limit), not the whole table. To get another page: get_all(db, skip=10, limit=5)
all_users = get_all(db)
print("users on this page:", len(all_users))
for user in all_users:
    print(user.id, user.name, user.email)


# --- Test 3: Get tasks, filtered by is_done ---
# Equivalent SQL: SELECT * FROM tasks WHERE is_done = TRUE ORDER BY id LIMIT 10;
# True = only done tasks. Pass False for unfinished, or leave it out for all.
# Also limited to 10 rows by default, so the count is at most 10.
all_tasks = get_tasks(db, True)
print("tasks on this page:", len(all_tasks))
for task in all_tasks:
    print(task.id, task.title, task.is_done, task.user_id)


# --- Test 4: Get one user by id ---
# Equivalent SQL: SELECT * FROM users WHERE id = 5;
# ⚠️ User 5 was deleted earlier, so this returns None and the next line
#    crashes with "'NoneType' object has no attribute 'name'".
#    Use an id that still exists, like 1.
search_by_user = get_user_by_id(db, 5)
print("userdetail", search_by_user.name, search_by_user.email)


# --- Test 5: Get one task by the