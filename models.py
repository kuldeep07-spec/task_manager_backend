from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

class User(Base):
    __tablename__="users"

    id=Column(Integer,primary_key=True,autoincrement=True)
    name=Column(String(200),nullable=False)
    email=Column(String(200),unique=True,nullable=False)


class Task(Base):
    __tablename__="task"

    id=Column(Integer,primary_key=True,autoincrement=True)
    title=Column(String(300),nullable=False)
    is_done=Column(Boolean,default=False)
    user_id=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"))