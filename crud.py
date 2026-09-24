from sqlalchemy.orm import Session
from models import User

# Creates a new user row in the database.
# Equivalent SQL: INSERT INTO users (name, email) VALUES (...);
def create_user(db: Session, name: str, email: str):
    new_user = User(name=name, email=email)  # build the row in memory (not saved yet)
    db.add(new_user)      # stage the change
    db.commit()            # actually save it to MySQL (same idea as SQL's COMMIT)
    db.refresh(new_user)   # reload from DB so new_user.id gets the real auto-generated value
    return new_user


def get_all(db:Session):
    return db.query(User).all()

def get_user_by_id(db:Session,user_id:int):
    return db.query(User).filter(User.id==user_id).first()
