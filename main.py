from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from crud import get_all, get_user_by_id, create_user, update_user_email, delete_user, get_tasks
# ⚠️ BUG TO FIND (1): this import list must match what crud.py really defines.
#    Open crud.py and read the function names. Does every name imported
#    above exist there? If one is missing, the app will not even start
#    (ImportError). Hint: look at the DELETE section of crud.py.
from pydantic import BaseModel


app = FastAPI()   # the app object. `uvicorn main:app` means "file main, object app"


# ═════════════════════════════════════════════════════════════════════════
# main.py : REVISION GUIDE (read this first)
# ═════════════════════════════════════════════════════════════════════════
# JOB OF THIS FILE
#   The HTTP door ("front desk"): routes, status codes, request validation.
#   It never writes SQL or queries. It calls a crud.py function, looks at
#   what came back, and decides the HTTP answer.
#
# THE PATTERN INSIDE EVERY ROUTE (same 3 beats, always)
#   1. Receive input (path / query / body) and get a session via Depends.
#   2. Call ONE crud function.
#   3. Check the result: None / False -> raise HTTPException, else return it.
#
# RESULT -> STATUS CODE TABLE
#   crud returns a row / list      -> 200 OK (FastAPI turns it into JSON)
#   crud returns None / False      -> 404 Not Found   (read / update / delete)
#   create_user returns None       -> 409 Conflict    (duplicate email)
#   body has the wrong type/shape  -> 422 (FastAPI does this by itself)
#   anything unexpected crashes    -> 500 (a bug, or the DB is down)
#
# ROUTES IN THIS FILE
#   GET    /                    home (health check)
#   GET    /users               one page of users
#   GET    /tasks               one page of tasks, optional ?is_done filter
#   GET    /users/{user_id}     one user          (404 if missing)
#   GET    /users/{user_id}/tasks   that user's tasks (404 if no such user)
#   POST   /users               create user       (409 if email exists)
#   PUT    /users/{user_id}     change email      (404 if missing)
#   DELETE /users/{user_id}     delete            (404 if missing)
#
# REVISION METHOD
#   Cover the code, rewrite one route from a blank file, then compare.
#   Easiest first: read_user -> list_users -> list_tasks -> update -> create.
# ═════════════════════════════════════════════════════════════════════════


# Pydantic models describe the SHAPE of incoming request bodies.
# These are not database tables (that's models.py) — just a check on
# what a request must contain before FastAPI lets it reach your function.
# If the body is missing a field or has the wrong type, FastAPI answers
# 422 automatically and your function never runs.
# Rule of thumb:  models.py = what is STORED.   Pydantic class = what is SENT.

class UserCreate(BaseModel):
    name: str     # required text. Missing or a wrong type -> 422
    email: str    # required text (any string for now; format is not checked)


class UserUpdate(BaseModel):
    email: str    # update only needs the new email. The id comes from the URL.


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
#
# WHERE THE CHECK LIVES: here, not in crud.py. 404 is an HTTP idea, and
# crud.py must know nothing about HTTP. crud.py only says "None"; this file
# decides what None means for the client.


# ─────────────────────────────────────────────
# Path parameters vs query parameters
# ─────────────────────────────────────────────
# FastAPI decides by one rule, based on the route string:
#   - name appears in {} in the route  -> PATH parameter   (/users/5)
#   - name does NOT appear in the route -> QUERY parameter (/users?skip=10&limit=5)
#   - a parameter whose type is a Pydantic class -> request BODY (JSON)
# A "= value" after a parameter is its default, used when the caller sends nothing.
# A type hint is also validation: /users/abc with user_id: int -> 422 for free.


# ─────────────────────────────────────────────
# GET routes — read data, never change anything
# ─────────────────────────────────────────────

# Health check. No database, no parameters. Useful to confirm the server is up.
@app.get("/")
def home():
    return {"message": "Task Manager API is running"}   # a dict becomes JSON


# Pagination: returns one page of users instead of the whole table.
# skip  = rows to skip first (OFFSET).  Formula: skip = (page - 1) * page_size
# limit = rows to return (LIMIT, the page size)
# Example: /users?skip=10&limit=5 -> page 3 with 5 users per page.
# Plain /users uses the defaults (skip=0, limit=10) -> first 10 users.
# An empty page returns [] with 200 (an empty list is a valid answer, not a 404).
# README note: OFFSET gets slower on huge tables because PostgreSQL still
# walks past the skipped rows. Fine for now; keyset pagination is the later fix.
# IMPROVE LATER: nothing stops ?limit=1000000. Cap it (e.g. max 100).
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
# FastAPI converts the text "true"/"false" in the URL into a real bool.
# `bool | None` means "a bool, or nothing sent". None = do not filter.
@app.get("/tasks")
def list_tasks(is_done: bool | None = None, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_tasks(db, is_done=is_done, skip=skip, limit=limit)


# One user by id. Route text /users/5 -> user_id = 5 (already converted to int).
# Edge cases: id not found -> 404.  id = "abc" -> 422 (automatic).
@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    # {user_id} in the route path becomes the user_id argument here.
    user = get_user_by_id(db, user_id)      # a User object, or None
    if not user:                            # a real User object is always truthy
        raise HTTPException(status_code=404, detail="User not found")
    return user


# All tasks belonging to one user.
# Two different "nothing" answers, on purpose:
#   user does not exist          -> 404
#   user exists but has no tasks -> 200 with []
# That is why we look the user up FIRST instead of querying tasks directly.
@app.get("/users/{user_id}/tasks")
def read_user_tasks(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.tasks   # uses the relationship() from models.py — no manual query needed
    # user.tasks runs a SELECT on tasks for this user behind the scenes.
    # (It works here because the session is still open during the request.)


# ─────────────────────────────────────────────
# POST — create a new row
# ─────────────────────────────────────────────

# Creates a user from the JSON body {"name": "...", "email": "..."}.
# Success -> 200 with the saved user (including its new id).
# Duplicate email -> create_user returned None -> we answer 409 Conflict.
# README tradeoff: we do not check "email exists?" first. The DB UNIQUE rule
# decides, because two simultaneous requests could both pass a check.
@app.post("/users")
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    # FastAPI reads the request body, validates it against UserCreate,
    # and gives us `user` as a ready-to-use object.
    new_user = create_user(db, name=user.name, email=user.email)
    if new_user is None:
        raise HTTPException(status_code=409, detail="Email already exists")

    return create_user(db, name=user.name, email=user.email)
    # ⚠️ BUG TO FIND (2): count how many times create_user is called in this
    #    function. Now think: what happens on the SECOND call with the same
    #    email? Test it in /docs with a brand-new email and look at what the
    #    response body says, and what is in the database.


# ─────────────────────────────────────────────
# PUT — update an existing row
# ─────────────────────────────────────────────

# Changes one user's email. The id comes from the URL, the new email from the body.
# Not found -> 404.
# KNOWN GAP: if the new email belongs to another user, crud's commit raises
# IntegrityError and this route returns 500. Same cure as create (see crud.py).
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

# Deletes a user by id. crud returns True (deleted) or False (not found).
# Success returns a small message, because the row no longer exists to send back.
# (Deleting a user also deletes their tasks: ON DELETE CASCADE in the database.)
@app.delete("/users/{user_id}")
def delete_user_route(user_id: int, db: Session = Depends(get_db)):
    # Named delete_user_route, not delete_user, so it doesn't shadow
    # the delete_user function imported from crud.py above.
    deleted = delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": f"User {user_id} deleted"}