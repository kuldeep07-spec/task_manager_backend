from database import SessionLocal
from crud import create_user

db = SessionLocal()
new_user = create_user(db, name="Test Python User", email="testpython@example.com")
print("Created user with id:", new_user.id)
db.close()