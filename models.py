from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
# Column      -> declares one column in a table
# Integer, String, Boolean -> the column's data type (INT, VARCHAR, BOOLEAN in MySQL)
# ForeignKey  -> links a column to another table's column

from sqlalchemy.orm import relationship
# relationship -> lets objects reach related rows (user.tasks, task.owner)
#                 without writing a JOIN by hand

from database import Base
# Base -> the parent class from database.py. Inheriting from it is what
#         tells SQLAlchemy "this class is a database table".


# ─────────────────────────────────────────────
# USERS table
# ─────────────────────────────────────────────
# Each attribute below maps to one column in MySQL.
class User(Base):
    __tablename__ = "users"  # must match the real table name in MySQL exactly

    id = Column(Integer, primary_key=True, autoincrement=True)  # AUTO_INCREMENT PRIMARY KEY
    name = Column(String(200), nullable=False)                   # NOT NULL
    email = Column(String(200), unique=True, nullable=False)     # UNIQUE NOT NULL

    # Relationship (Python-only, adds no column, changes nothing in MySQL).
    # Gives every user a "tasks" shelf: user.tasks -> list of their Task rows.
    # "Task" is the CLASS name (not the table name).
    # back_populates="owner" tells SQLAlchemy the matching attribute on Task
    # is called "owner" (see below). The spelling must match exactly.
    #
    # passive_deletes=True: when a user is deleted, don't let SQLAlchemy touch
    # their tasks first. Without it, SQLAlchemy sets each task's user_id to NULL
    # before deleting the user, so MySQL's ON DELETE CASCADE has nothing left
    # to delete and the tasks stay behind as orphans. With it, SQLAlchemy leaves
    # the cleanup to MySQL's cascade, which then deletes the tasks.
    tasks = relationship("Task", back_populates="owner", passive_deletes=True)


# ─────────────────────────────────────────────
# TASKS table
# ─────────────────────────────────────────────
# Each task belongs to exactly one user (one-to-many: one user, many tasks).
class Task(Base):
    __tablename__ = "tasks"  # matches the real MySQL table name

    id = Column(Integer, primary_key=True, autoincrement=True)  # AUTO_INCREMENT PRIMARY KEY
    title = Column(String(300), nullable=False)                  # NOT NULL
    is_done = Column(Boolean, default=False)                     # matches DEFAULT FALSE in MySQL

    # Links to users.id. Note the string uses the TABLE name ("users"),
    # not the class name ("User"). ForeignKey speaks MySQL, relationship speaks Python.
    # ondelete="CASCADE" matches our MySQL FK: if a user is deleted,
    # MySQL deletes all their tasks too.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    # Relationship (Python-only, adds no column, changes nothing in MySQL).
    # Gives every task an "owner" shelf: task.owner -> the single User who owns it.
    # back_populates="tasks" tells SQLAlchemy the matching attribute on User
    # is called "tasks" (see above). Together, these two lines let you walk
    # the link in both directions without writing a JOIN by hand.
    # task.owner is ONE user (a task has one owner); user.tasks is a LIST.
    owner = relationship("User", back_populates="tasks")