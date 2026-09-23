# Quick sanity check: confirms models.py has no import/syntax errors,
# and that each class is correctly linked to its real MySQL table name.
from models import User, Task

print("Models imported successfully!")
print("User table:", User.__tablename__)
print("Task table:", Task.__tablename__)