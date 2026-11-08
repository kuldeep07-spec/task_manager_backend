from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
# Column      -> declares one column in a table
# Integer, String, Boolean -> the column's data type (INT, VARCHAR, BOOLEAN in PostgreSQL)
# ForeignKey  -> links a column to another table's column
from sqlalchemy.dialects.postgresql import JSONB
# JSONB -> PostgreSQL's flexible JSON column type.
#          NOT USED in this file right now (the `extra` column was removed),
#          so this import is harmless but could be deleted.

from sqlalchemy.orm import relationship
# relationship -> lets objects reach related rows (user.tasks, task.owner)
#                 without writing a JOIN by hand

from database import Base
# Base -> the parent class from database.py. Inheriting from it is what
#         tells SQLAlchemy "this class is a database table".

# ═════════════════════════════════════════════════════════════════════════
# models.py : REVISION GUIDE (read this first)
# ═════════════════════════════════════════════════════════════════════════
# JOB OF THIS FILE
#   Describes your tables as Python classes. It is the CREATE TABLE of your
#   project, written in Python. It holds NO queries and NO HTTP code.
#
# WHO USES IT
#   crud.py        -> imports User, Task to run queries (db.query(User)...)
#   alembic/env.py -> reads these models (through Base) to autogenerate migrations
#
# IMPORTANT: A MODEL CHANGE IS NOT A DATABASE CHANGE
#   Editing this file does not touch PostgreSQL. To change the real table:
#   edit the model -> alembic revision --autogenerate -> READ the file
#   -> alembic upgrade head.
#
# CHEAT TABLE (Python <-> SQL)
#   class User(Base) + __tablename__    -> CREATE TABLE users
#   Column(Integer, primary_key=True)   -> PRIMARY KEY
#   Column(String(200), nullable=False) -> VARCHAR(200) NOT NULL
#   unique=True                         -> UNIQUE (duplicates refused)
#   ForeignKey("users.id")              -> links to TABLE users, column id
#   ondelete="CASCADE"                  -> DB deletes a user's tasks with the user
#   index=True                          -> CREATE INDEX (FKs are NOT auto-indexed)
#   relationship(...)                   -> a JOIN in Python (adds no column)
#
# THREE BUGS TO CHECK WHEN SOMETHING BREAKS (from the bug-hunt drill)
#   1. back_populates text must match the other side's attribute name exactly.
#   2. ForeignKey("table.column") uses the TABLE name, not the class name.
#   3. unique=True missing -> no error, but duplicate emails get in silently.
# ═════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────
# USERS table
# ─────────────────────────────────────────────
# Each attribute below maps to one column in PostgreSQL.
class User(Base):
    __tablename__ = "users"  # must match the real table name in PostgreSQL exactly

    id = Column(Integer, primary_key=True, autoincrement=True)  # auto-generated id (identity column) + PRIMARY KEY
    # ↑ You never set the id yourself. PostgreSQL generates it on INSERT, which is why
    #   crud.py calls db.refresh() after commit to read it back.
    #   Failed inserts also use up numbers, so gaps in ids are normal.
    name = Column(String(200), nullable=False)                   # VARCHAR(200) NOT NULL (name is required)
    email = Column(String(200), unique=True, nullable=False)     # UNIQUE NOT NULL
    # ↑ unique=True is what makes a duplicate email raise IntegrityError,
    #   which crud.py catches and main.py turns into a 409.
    #   Without it, duplicates would be saved silently (no error at all).

    # Relationship (Python-only, adds no column, changes nothing in PostgreSQL).
    # Gives every user a "tasks" shelf: user.tasks -> list of their Task rows.
    # "Task" is the CLASS name (not the table name).
    # back_populates="owner" tells SQLAlchemy the matching attribute on Task
    # is called "owner" (see below). The spelling must match exactly,
    # or the app crashes at startup.
    #
    # passive_deletes=True: when a user is deleted, don't let SQLAlchemy touch
    # their tasks first. Without it, SQLAlchemy sets each task's user_id to NULL
    # before deleting the user, so PostgreSQL's ON DELETE CASCADE has nothing left
    # to delete and the tasks stay behind as orphans. With it, SQLAlchemy leaves
    # the cleanup to PostgreSQL's cascade, which then deletes the tasks.
    tasks = relationship("Task", back_populates="owner", passive_deletes=True)


# ─────────────────────────────────────────────
# TASKS table
# ─────────────────────────────────────────────
# Each task belongs to exactly one user (one-to-many: one user, many tasks).
class Task(Base):
    __tablename__ = "tasks"  # matches the real PostgreSQL table name

    id = Column(Integer, primary_key=True, autoincrement=True)  # auto-generated id + PRIMARY KEY
    title = Column(String(300), nullable=False)                  # NOT NULL
    is_done = Column(Boolean, default=False)                     # new tasks start as not done
    # ↑ default=False is applied by SQLAlchemy when you create a Task without is_done.
    #   Note: this is a Python-side default, not a DEFAULT clause on the column
    #   itself (only matters if rows are inserted outside SQLAlchemy, e.g. in psql).

    # Links to users.id. Note the string uses the TABLE name ("users"),
    # not the class name ("User"). ForeignKey speaks SQL, relationship speaks Python.
    # ondelete="CASCADE" matches our PostgreSQL FK: if a user is deleted,
    # PostgreSQL deletes all their tasks too.
    # index=True: PostgreSQL does NOT index foreign keys automatically. This index
    # makes "all tasks of user X" fast (test: 500k rows, 45 ms -> 0.9 ms).
    # Tradeoff: slightly slower writes and a bit more disk. On our 140-row table
    # the planner still picks a Seq Scan, because reading the whole table is cheaper.
    # This was added later through an Alembic migration (ix_tasks_user_id).
    # nullable is not set, so user_id may be NULL (a task with no owner is allowed).
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),index=True)


    # Relationship (Python-only, adds no column, changes nothing in PostgreSQL).
    # Gives every task an "owner" shelf: task.owner -> the single User who owns it.
    # back_populates="tasks" tells SQLAlchemy the matching attribute on User
    # is called "tasks" (see above). Together, these two lines let you walk
    # the link in both directions without writing a JOIN by hand.
    # task.owner is ONE user (a task has one owner); user.tasks is a LIST.
    owner = relationship("User", back_populates="tasks")