import logging
import sys
from pathlib import Path
from typing import List

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.models import User, Role
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """
    Initialize the database with required tables and initial data.
    """
    # Create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

def create_initial_roles(db: Session) -> List[Role]:
    """Create initial roles if they don't exist."""
    roles = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "moderator", "description": "Moderator with limited admin access"},
        {"name": "user", "description": "Regular user"},
    ]
    
    created_roles = []
    for role_data in roles:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
            logger.info(f"Created role: {role.name}")
        created_roles.append(role)
    
    db.commit()
    return created_roles

def create_initial_admin(db: Session) -> User:
    """Create initial admin user if it doesn't exist."""
    admin_email = "admin@example.com"
    admin_password = "admin"  # In production, this should be changed after first login
    
    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
        )
        admin.set_password(admin_password)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info(f"Created admin user with email: {admin_email}")
    
    # Ensure admin has admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if admin_role and admin_role not in admin.roles:
        admin.roles.append(admin_role)
        db.commit()
        logger.info(f"Assigned admin role to user: {admin_email}")
    
    return admin

def main() -> None:
    """Main function to initialize the database."""
    logger.info("Starting database initialization...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize database
        init_db(db)
        
        # Create initial data
        create_initial_roles(db)
        create_initial_admin(db)
        
        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
