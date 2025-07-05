"""
Tests for authentication endpoints.
"""
from typing import Dict, Any
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User
from app.schemas.token import Token

def test_login_success(client: TestClient, test_user: User) -> None:
    """Test successful user login."""
    login_data = {
        "username": test_user.email,
        "password": "testpassword"
    }
    response = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in data
    
    # Verify the token is valid
    token_data = jwt.decode(
        data["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    assert token_data["sub"] == str(test_user.id)


def test_login_wrong_password(client: TestClient, test_user: User) -> None:
    """Test login with wrong password."""
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword"
    }
    response = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "incorrect email or password" in response.json()["detail"].lower()


def test_login_inactive_user(client: TestClient, db_session: Session) -> None:
    """Test login with inactive user."""
    # Create an inactive user
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Inactive User",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "username": user.email,
        "password": "testpassword"
    }
    response = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "inactive" in response.json()["detail"].lower()


def test_login_nonexistent_user(client: TestClient) -> None:
    """Test login with non-existent user."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "testpassword"
    }
    response = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "incorrect email or password" in response.json()["detail"].lower()


def test_refresh_token(client: TestClient, test_user: User) -> None:
    """Test refreshing an access token."""
    # First login to get a refresh token
    login_data = {
        "username": test_user.email,
        "password": "testpassword"
    }
    login_response = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Now refresh the token
    response = client.post(
        "/api/v1/auth/refresh-token",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify the new access token is valid
    token_data = jwt.decode(
        data["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    assert token_data["sub"] == str(test_user.id)


def test_refresh_token_invalid(client: TestClient) -> None:
    """Test refreshing with an invalid refresh token."""
    response = client.post(
        "/api/v1/auth/refresh-token",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid token" in response.json()["detail"].lower()


def test_refresh_token_expired(client: TestClient, test_user: User) -> None:
    """Test refreshing with an expired refresh token."""
    # Create an expired refresh token
    expired_token = create_access_token(
        subject=str(test_user.id),
        expires_delta=timedelta(minutes=-5)  # Expired 5 minutes ago
    )
    
    response = client.post(
        "/api/v1/auth/refresh-token",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in response.json()["detail"].lower()


def test_logout(client: TestClient, test_user: User) -> None:
    """Test user logout."""
    # First login to get a token
    login_data = {
        "username": test_user.email,
        "password": "testpassword"
    }
    login_response = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = login_response.json()["access_token"]
    
    # Now logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "successfully logged out" in response.json()["message"].lower()
    
    # Verify the token is now blacklisted
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_user(client: TestClient, db_session: Session) -> None:
    """Test user registration."""
    # Create a user role if it doesn't exist
    user_role = db_session.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(name="user", description="Regular user")
        db_session.add(user_role)
        db_session.commit()
    
    user_data = {
        "email": "newuser@example.com",
        "password": "Testpassword123!",  # Strong password
        "full_name": "New Test User"
    }
    
    response = client.post(
        "/api/v1/auth/register",
        json=user_data
    )
    
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
    assert verify_password(user_data["password"], user.hashed_password)
    assert user.is_active is True
    assert len(user.roles) == 1
    assert user.roles[0].name == "user"


def test_register_existing_email(client: TestClient, test_user: User) -> None:
    """Test registering with an existing email."""
    user_data = {
        "email": test_user.email,  # Already exists
        "password": "Testpassword123!",
        "full_name": "Duplicate User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email already registered" in response.json()["detail"].lower()


def test_register_invalid_email(client: TestClient) -> None:
    """Test registering with an invalid email format."""
    user_data = {
        "email": "not-an-email",
        "password": "Testpassword123!",
        "full_name": "Invalid Email"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "value is not a valid email address" in str(response.json()).lower()


def test_register_weak_password(client: TestClient) -> None:
    """Test registering with a weak password."""
    user_data = {
        "email": "weakpass@example.com",
        "password": "weak",
        "full_name": "Weak Password"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "password" in str(response.json()).lower()


def test_get_current_user(client: TestClient, test_user: User) -> None:
    """Test getting the current user with a valid token."""
    # First login to get a token
    login_data = {
        "username": test_user.email,
        "password": "testpassword"
    }
    login_response = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert "hashed_password" not in data


def test_get_current_user_unauthorized(client: TestClient) -> None:
    """Test getting the current user without a token."""
    response = client.get("/api/v1/users/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "not authenticated" in response.json()["detail"].lower()


def test_get_current_user_invalid_token(client: TestClient) -> None:
    """Test getting the current user with an invalid token."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid token" in response.json()["detail"].lower()
