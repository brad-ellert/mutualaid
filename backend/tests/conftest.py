"""
Pytest configuration and fixtures for testing the FastAPI application.
"""
import os
import sys
from pathlib import Path
from typing import Generator, Callable, Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.base import Base
from app.main import app, get_db
from app.models import User, Role
from app.core.security import get_password_hash

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)

# Override the get_db dependency to use the test database
def override_get_db() -> Generator[SQLAlchemySession, None, None]:
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()

app.dependency_overrides[get_db] = override_get_db

# Test client
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

# Test database session with nested transactions for rollback
@pytest.fixture(scope="function")
def db_session() -> Generator[SQLAlchemySession, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Start a nested transaction
    session.begin_nested()
    
    # Allow nested transactions for rollback
    @event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(sess: SQLAlchemySession, transaction_: Any) -> None:
        if transaction_.nested and not transaction_._parent.nested:
            session.begin_nested()
    
    yield session
    
    # Clean up
    session.close()
    transaction.rollback()
    connection.close()

# Test admin user
@pytest.fixture(scope="function")
def test_admin(db_session: SQLAlchemySession) -> User:
    # Create roles if they don't exist
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="Administrator")
        db_session.add(admin_role)
        db_session.commit()
    
    # Create admin user
    admin = db_session.query(User).filter(User.email == "admin@test.com").first()
    if not admin:
        admin = User(
            email="admin@test.com",
            full_name="Test Admin",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
            is_superuser=True
        )
        admin.roles.append(admin_role)
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    
    return admin

# Test regular user
@pytest.fixture(scope="function")
def test_user(db_session: SQLAlchemySession) -> User:
    # Create roles if they don't exist
    user_role = db_session.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(name="user", description="Regular user")
        db_session.add(user_role)
        db_session.commit()
    
    # Create regular user
    user = db_session.query(User).filter(User.email == "user@test.com").first()
    if not user:
        user = User(
            email="user@test.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
            is_superuser=False
        )
        user.roles.append(user_role)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    return user

# Authenticated test client
@pytest.fixture(scope="function")
def auth_client(client: TestClient, test_user: User) -> TestClient:
    # Get login token
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Set auth header for subsequent requests
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client

# Admin authenticated test client
@pytest.fixture(scope="function")
def admin_client(client: TestClient, test_admin: User) -> TestClient:
    # Get login token
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_admin.email, "password": "testpassword"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Set auth header for subsequent requests
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
