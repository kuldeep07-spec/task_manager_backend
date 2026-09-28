from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# This class represents the "users" table.
# Each attribute below maps to one column in MySQL.
class User(Base):
    __tablename__ = "users"  # must match the real table name in MySQL exactly

    id = Column(Integer, primary_key=True, autoincrement=True)  # AUTO_INCREMENT PRIMARY KEY
    name = Column(String(200), nullable=False)                   # NOT NULL
    email = Column(String(200), unique=True, nullable=False)     # UNIQUE NOT NULL

    # Relationship (Python-only, adds no column, changes nothing in MySQL).
    # Gives every user a "tasks" shelf: user.tasks -> list of their Task rows.
    # back_populates="owner" tells SQLAlchemy the matching attribute on Task
    # is called "owner" (see below).
    tasks = relationship("Task", back_populates="owner")


# This class represents the "tasks" table.
# It has a foreign key linking each task back to the user who owns it.
class Task(Base):
    __tablename__ = "tasks"  # matches the real MySQL table name

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    is_done = Column(Boolean, default=False)  # matches DEFAULT FALSE in MySQL

    # Links to users.id. ondelete="CASCADE" matches our MySQL FK:
    # if a user is deleted, all their tasks get deleted too.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    # Relationship (Python-only, adds no column, changes nothing in MySQL).
    # Gives every task an "owner" shelf: task.owner -> the single User who owns it.
    # back_populates="tasks" tells SQLAlchemy the matching attribute on User
    # is called "tasks" (see above). Together, these two lines let you walk
    # the link in both directions without writing a JOIN by hand.
    owner = relationship("User", back_populates="tasks")