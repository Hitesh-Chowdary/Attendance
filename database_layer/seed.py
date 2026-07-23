import sys
import os
from passlib.context import CryptContext

# Adjust sys.path to run directly from the workspace root or directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_layer.connection import engine, Base, SessionLocal
from database_layer.models import Teacher

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def seed_database():
    print("Initialising database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if System Admin account exists; if not, create initial Admin user
        admin = db.query(Teacher).filter(Teacher.email == "admin@college.edu").first()
        if not admin:
            print("Creating default System Admin account (admin@college.edu)...")
            admin_user = Teacher(
                name="System Administrator",
                email="admin@college.edu",
                password_hash=get_password_hash("admin123")
            )
            db.add(admin_user)
            db.commit()
            print("Default System Admin account created successfully!")
        else:
            print("Database initialised. Admin account ready.")

    except Exception as e:
        print("Error initialising database:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
