# Quick check that Python can actually reach the MySQL database
# using the engine defined in database.py.
from database import engine

try:
    connection = engine.connect()
    print("Connected successfully!")
    connection.close()
except Exception as e:
    print("Connection failed:", e)