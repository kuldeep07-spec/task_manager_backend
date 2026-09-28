# relationship_test.py
# Manual test for the two relationship() links added to models.py:
#   person.tasks  -> a user's list of tasks (the "one" side, list of "many")
#   work.owner    -> a task's single owner  (the "many" side, one object)
#
# ⚠️ Requires:
#   - a user id that still exists (user 2 was deleted, use a different id)
#   - get_task_by_id() to exist in crud.py (not written yet as of this version)

from database import SessionLocal
from crud import get_user_by_id, get_task_by_id

db = SessionLocal()  # open a real session/connection


# --- Test A: user -> tasks (the "tasks" shelf on User) ---
# Equivalent to: SELECT * FROM tasks WHERE user_id = <person's id>;
# but triggered automatically by SQLAlchemy when person.tasks is accessed.
person = get_user_by_id(db, 2)
print("person:", person.name)

for x in person.tasks:
    print(x.id, x.title)


# --- Test B: task -> owner (the "owner" shelf on Task) ---
# Equivalent to: SELECT * FROM users WHERE id = <task's user_id>;
# but triggered automatically by SQLAlchemy when work.owner is accessed.
work = get_task_by_id(db, 1)
print(work.title, work.owner.name)


db.close()  # always close the session when done