from sqlalchemy import create_engine                         # builds the connection to the database
from sqlalchemy.orm import sessionmaker, declarative_base    # session factory + parent class for models
from dotenv import load_dotenv                               # reads the .env file
import os                                                    # reads environment variables

# ═════════════════════════════════════════════════════════════════════════
# database.py : REVISION GUIDE (read this first)
# ═════════════════════════════════════════════════════════════════════════
# JOB OF THIS FILE
#   The connection setup. It does not know about users or tasks.
#   Think of it as "opening the shop": the road to PostgreSQL (engine),
#   a counter for each customer (session), and the parent of all models (Base).
#
# WHO USES WHAT
#   models.py -> imports Base      (every model class inherits from it)
#   main.py   -> imports get_db    (used as Depends(get_db) in routes)
#   alembic/env.py -> imports Base and DATABASE_URL (to compare models with the DB)
#
# THE FLOW
#   .env -> DATABASE_URL -> engine -> SessionLocal -> get_db() -> db in a route
#
# NO NEED TO MEMORISE THE LINES
#   This is boilerplate: copy it from the last project. Remember the four
#   roles: engine = connection, SessionLocal = session factory,
#   Base = parent of models, get_db = one session per request.
# ═════════════════════════════════════════════════════════════════════════

# Load variables from the .env file into the environment
load_dotenv()
# ↑ Reads the .env file and puts each line (KEY=value) into the environment.
#   Without this call, os.getenv below would find nothing.

# Read the connection string from the environment instead of hardcoding it here.
# This keeps the real password out of the code itself (and out of GitHub).
DATABASE_URL = os.getenv("DATABASE_URL")
# ↑ The value in .env looks like:
#     postgresql+psycopg2://USER:PASSWORD@localhost:5432/test_db
#   Parts: database type + driver // user : password @ host : port / database name
#   (PostgreSQL's default port is 5432; MySQL's was 3306.)
#   GOTCHA: if .env is missing or the name is misspelled, this is None, and
#   create_engine below fails with an error. Check .env first when it breaks.
#   GOTCHA: .env must be in .gitignore, or the password goes to GitHub.

engine = create_engine(DATABASE_URL,echo=True)
# ↑ The engine = the connection to PostgreSQL (SQL world: "the connection").
#   It manages a pool of connections, so each request does not open a new one.
#   It is lazy: it connects only when the first query runs, not on this line.
#   Tip: create_engine(DATABASE_URL, echo=True) prints every SQL statement,
#   very useful for seeing what SQLAlchemy actually sends to the database.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# ↑ A FACTORY for sessions. SessionLocal() gives one new session.
#   A session = one conversation with the database (SQL's BEGIN ... COMMIT).
#   autocommit=False -> nothing is saved until you call db.commit().
#                       (Forget it and your change silently vanishes.)
#   autoflush=False  -> pending changes are not sent to the database
#                       automatically before each query; they go on commit.
#   bind=engine      -> every session made here uses this connection.

Base = declarative_base()
# ↑ The parent class of all models. In models.py: class User(Base): ...
#   Base keeps a list of every model, which is how Alembic's autogenerate
#   knows which tables should exist (it compares this list with the database).


# ─────────────────────────────────────────────
# get_db: one session per request
# ─────────────────────────────────────────────
# Used in routes as:  db: Session = Depends(get_db)
# FastAPI calls get_db(), gives the route the `db` it yields, and when the
# request is finished it runs the code after the yield (the finally block).
# Result: every request gets its own session, and it is ALWAYS closed,
# even when the route raised an error (404, 409, or a crash).
def get_db():
    db = SessionLocal()
    # ↑ Open a new session for this request.

    try:
        yield db
        # ↑ Hand the session to the route. The function PAUSES here while
        #   the route runs, and continues after the route has finished.
        #   (yield instead of return is what makes the cleanup possible.)
    finally:
        db.close()
        # ↑ Always runs, success or error. Returns the connection to the pool.
        #   Without it, connections leak, and under load the pool runs out
        #   and requests hang. Note: close() does NOT commit. Uncommitted
        #   changes are thrown away, which is why crud.py calls db.commit().