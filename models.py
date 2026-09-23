from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

# This class represents the "users" table.
# Each attribute below maps to one column in MySQL.
class User(Base):
    __tablename__ = "users"  # must match the real table name in MySQL exactly

    id = Column(Integer, primary_key=True, autoincrement=True)  # AUTO_INCREMENT PRIMARY KEY
    name = Column(String(200), nullable=False)                   # NOT NULL
    email = Column(String(200), unique=True, nullable=False)     # UNIQUE NOT NULL


# This class represents the "task" table.
# It has a foreign key linking each task back to the user who owns it.
class Task(Base):
    __tablename__ = "task"  # matches the real MySQL table name (singular, not "tasks")

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    is_done = Column(Boolean, default=False)  # matches DEFAULT FALSE in MySQL

    # Links to users.id. ondelete="CASCADE" matches our MySQL FK:
    # if a user is deleted, all their tasks get deleted too.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))