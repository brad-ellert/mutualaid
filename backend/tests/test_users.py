"""
Tests for user-related endpoints.
"""
from typing import Dict, Any, List
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Role
from app.schemas.user import UserCreate, UserUpdate, UserInDB
from app.core.security import get_password_hash

def test_create_user(client: TestClient, db_session: Session) -> None:
    """Test creating a new user."""
    # Create a user role if it doesn't exist
    user_role = db_session.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(name="user", description="Regular user")
        db_session.add(user_role)
        db_session.commit()
    
    user_data = {
        "email": "newuser@example.com",
        "password": "testpassword123",
        "full_name": "New Test User",
        "is_active": True
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "hashed_password" not in data
    assert data["is_active"] is True
    assert "id" in data
    
    # Verify the user was created in the database
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    assert user is not None
    assert user.email == user_data["email"]
    assert user.full_name == user_data["full_name"]
    assert user.is_active is True
    assert verify_password(user_data["password"], user.hashed_password)


def test_create_user_existing_email(client: TestClient, test_user: User) -> None:
    """Test creating a user with an existing email."""
    user_data = {
        "email": test_user.email,  # This email already exists
        "password": "testpassword123",
        "full_name": "Duplicate User"
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()


def test_read_users(admin_client: TestClient, test_user: User, db_session: Session) -> None:
    """Test retrieving a list of users (admin only)."""
    # Create a second test user
    user2 = User(
        email="user2@example.com",
        full_name="User Two",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user2)
    db_session.commit()
    
    response = admin_client.get("/api/v1/users/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least admin and test_user
    
    # Convert to dict for easier searching
    user_emails = [user["email"] for user in data]
    assert test_user.email in user_emails
    assert "user2@example.com" in user_emails
    
    # Verify sensitive data is not exposed
    for user in data:
        assert "hashed_password" not in user
        assert "password" not in user


def test_read_users_unauthorized(auth_client: TestClient) -> None:
    """Test that regular users cannot list all users."""
    response = auth_client.get("/api/v1/users/")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_user(admin_client: TestClient, test_user: User) -> None:
    """Test retrieving a specific user by ID."""
    response = admin_client.get(f"/api/v1/users/{test_user.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert "hashed_password" not in data


def test_read_user_not_found(admin_client: TestClient) -> None:
    """Test retrieving a non-existent user."""
    response = admin_client.get("/api/v1/users/999999")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_update_user(auth_client: TestClient, test_user: User, db_session: Session) -> None:
    """Test updating a user's own information."""
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    
    response = auth_client.put(f"/api/v1/users/{test_user.id}", json=update_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]
    assert data["id"] == test_user.id
    
    # Verify the update in the database
    db_user = db_session.query(User).filter(User.id == test_user.id).first()
    assert db_user is not None
    assert db_user.full_name == update_data["full_name"]
    assert db_user.email == update_data["email"]


def test_update_password(auth_client: TestClient, test_user: User, db_session: Session) -> None:
    """Test updating a user's password."""
    new_password = "newpassword123"
    update_data = {
        "password": new_password
    }
    
    response = auth_client.put(f"/api/v1/users/{test_user.id}", json=update_data)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Verify the password was updated in the database
    db_user = db_session.query(User).filter(User.id == test_user.id).first()
    assert db_user is not None
    assert verify_password(new_password, db_user.hashed_password)


def test_update_other_user_unauthorized(auth_client: TestClient, db_session: Session) -> None:
    """Test that users cannot update other users' information."""
    # Create another user
    other_user = User(
        email="other@example.com",
        full_name="Other User",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(other_user)
    db_session.commit()
    
    update_data = {"full_name": "Should Not Work"}
    response = auth_client.put(f"/api/v1/users/{other_user.id}", json=update_data)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Verify the user was not updated
    db_user = db_session.query(User).filter(User.id == other_user.id).first()
    assert db_user is not None
    assert db_user.full_name == "Other User"


def test_delete_user(admin_client: TestClient, test_user: User, db_session: Session) -> None:
    """Test deleting a user (admin only)."""
    # Create a user to delete
    user_to_delete = User(
        email="todelete@example.com",
        full_name="To Be Deleted",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user_to_delete)
    db_session.commit()
    
    response = admin_client.delete(f"/api/v1/users/{user_to_delete.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user_to_delete.id
    assert data["email"] == user_to_delete.email
    
    # Verify the user was actually deleted
    assert db_session.query(User).filter(User.id == user_to_delete.id).first() is None


def test_delete_user_unauthorized(auth_client: TestClient, db_session: Session) -> None:
    """Test that regular users cannot delete other users."""
    # Create a user to delete
    user_to_delete = User(
        email="todelete2@example.com",
        full_name="To Be Deleted 2",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user_to_delete)
    db_session.commit()
    
    response = auth_client.delete(f"/api/v1/users/{user_to_delete.id}")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Verify the user was not deleted
    assert db_session.query(User).filter(User.id == user_to_delete.id).first() is not None


def test_update_user_roles(admin_client: TestClient, test_user: User, db_session: Session) -> None:
    """Test updating a user's roles (admin only)."""
    # Create a role if it doesn't exist
    role = db_session.query(Role).filter(Role.name == "moderator").first()
    if not role:
        role = Role(name="moderator", description="Moderator role")
        db_session.add(role)
        db_session.commit()
    
    update_data = {
        "role_ids": [role.id]
    }
    
    response = admin_client.put(f"/api/v1/users/{test_user.id}/roles", json=update_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["roles"]) == 1
    assert data["roles"][0]["name"] == "moderator"
    
    # Verify the role was assigned in the database
    db_user = db_session.query(User).filter(User.id == test_user.id).first()
    assert db_user is not None
    assert len(db_user.roles) == 1
    assert db_user.roles[0].name == "moderator"
