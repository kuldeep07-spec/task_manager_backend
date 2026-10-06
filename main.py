from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from crud import get_all, get_user_by_id, create_user, update_user_email, delete_user, get_tasks
from pydantic import BaseModel


app = FastAPI()


# Pydantic models describe the SHAPE of incoming request bodies.
# These are not database tables (that's models.py) — just a check on
# what a request must contain before FastAPI lets it reach your function.

class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    email: str


# ─────────────────────────────────────────────
# Why 404, and what it actually fixes
# ─────────────────────────────────────────────
# Every get_user_by_id-based function can return None if no row matches.
# Without a check, `return user` just hands None straight back to FastAPI,
# which turns it into `null` with a normal success status (200 OK). That's
# misleading — the caller has no clean way to tell "it worked, the answer
# is nothing" apart from "it failed, nothing exists."
#
# HTTPException stops the function immediately and tells FastAPI to send
# back:
#   - a specific status code (404), the standard HTTP code for "not found"
#   - a message (detail) explaining why
#
# A real client (a frontend app, or /docs) can check the status code and
# know for certain whether the request succeeded, instead of guessing
# from the shape of the response body.
#
# One line version: if not user: raise HTTPException(...) turns a silent
# null into an honest, clearly labeled "this doesn't exist" response.
# This same pattern repeats in every route below that can fail to find a row.


# ─────────────────────────────────────────────
# Path parameters vs query parameters
# ─────────────────────────────────────────────
# FastAPI decides by one rule, based on the route string:
#   - name appears in {} in the route  -> PATH parameter   (/users/5)
#   - name does NOT appear in the route -> QUERY parameter (/users?skip=10&limit=5)
# A "= value" after a parameter is its default, used when the caller sends nothing.


# ─────────────────────────────────────────────
# GET routes — read data, never change anything
# ─────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Task Manager API is running"}


# Pagination: returns one page of users instead of the whole table.
# skip  = rows to skip first (OFFSET).  Formula: skip = (page - 1) * page_size
# limit = rows to return (LIMIT, the page size)
# Example: /users?skip=10&limit=5 -> page 3 with 5 users per page.
# Plain /users uses the defaults (skip=0, limit=10) -> first 10 users.
@app.get("/users")
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # Depends(get_db) -> FastAPI calls get_db() for us, hands us the
    # session as `db`, and closes it automatically when the request ends.
    return get_all(db, skip=skip, limit=limit)


# Filtering + pagination together.
# is_done is OPTIONAL (defaults to None):
#   /tasks                  -> all tasks
#   /tasks?is_done=true     -> only done tasks
#   /tasks?is_done=false    -> only unfinished tasks
# The filter runs first, then skip/limit take a page from the filtered rows:
#   /tasks?is_done=false&skip=0&limit=5 -> first 5 unfinished tasks
@app.get("/tasks")
def list_tasks(is_done: bool | None = None, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_tasks(db, is_done=is_done, skip=skip, limit=limit)


@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    # {user_id} in the route path becomes the user_id argument here.
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/{user_id}/tasks")
def read_user_tasks(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.tasks   # uses the relationship() from models.py — no manual query needed


# ─────────────────────────────────────────────
# POST — create a new row
# ─────────────────────────────────────────────

@app.post("/users")
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    # FastAPI reads the request body, validates it against UserCreate,
    # and gives us `user` as a ready-to-use object.
    return create_user(db, name=user.name, email=user.email)


# ─────────────────────────────────────────────
# PUT — update an existing row
# ─────────────────────────────────────────────

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    # user_id comes from the URL path; user comes from the request body.
    # FastAPI tells them apart automatically based on where each name
    # is declared.
    updated = update_user_email(db, user_id, user.email)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


# ─────────────────────────────────────────────
# DELETE — remove a row
# ─────────────────────────────────────────────

@app.delete("/users/{user_id}")
def delete_user_route(user_id: int, db: Session = Depends(get_db)):
    # Named delete_user_route, not delete_user, so it doesn't shadow
    # the delete_user function imported from crud.py above.
    deleted = delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": f"User {user_id} deleted"}