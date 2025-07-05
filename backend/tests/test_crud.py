"""
Tests for CRUD operations.
"""
from typing import List, Dict, Any
import pytest
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.security import verify_password, get_password_hash
from app.models import Role, User


def test_create_user(db_session: Session) -> None:
    """Test creating a new user via CRUD."""
    # Create a user role
    role = Role(name="user", description="Regular user")
    db_session.add(role)
    db_session.commit()
    
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "role_ids": [role.id]
    }
    user_in = schemas.UserCreate(**user_data)
    
    user = crud.user.create(db_session, obj_in=user_in)
    
    assert user.email == user_data["email"]
    assert user.full_name == user_data["full_name"]
    assert user.is_active == user_data["is_active"]
    assert user.is_superuser == user_data["is_superuser"]
    assert hasattr(user, "hashed_password")
    assert verify_password(user_data["password"], user.hashed_password)
    
    # Verify roles were assigned
    assert len(user.roles) == 1
    assert user.roles[0].name == "user"


def test_authenticate_user(db_session: Session) -> None:
    """Test user authentication via CRUD."""
    email = "auth@example.com"
    password = "testpassword"
    hashed_password = get_password_hash(password)
    
    # Create a test user directly in the database
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name="Auth User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Test successful authentication
    auth_user = crud.user.authenticate(
        db_session, email=email, password=password
    )
    assert auth_user is not None
    assert auth_user.email == email
    
    # Test wrong password
    wrong_auth = crud.user.authenticate(
        db_session, email=email, password="wrongpassword"
    )
    assert wrong_auth is False
    
    # Test non-existent user
    nonexistent_auth = crud.user.authenticate(
        db_session, email="nonexistent@example.com", password=password
    )
    assert nonexistent_auth is False
    
    # Test inactive user
    user.is_active = False
    db_session.commit()
    inactive_auth = crud.user.authenticate(
        db_session, email=email, password=password
    )
    assert inactive_auth is False


def test_get_user(db_session: Session) -> None:
    """Test retrieving a user by ID via CRUD."""
    # Create a test user directly
    user = User(
        email="get@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Get User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Test getting the user
    stored_user = crud.user.get(db_session, id=user.id)
    assert stored_user is not None
    assert stored_user.email == user.email
    assert stored_user.full_name == user.full_name
    assert stored_user.hashed_password == user.hashed_password
    
    # Test non-existent user
    non_existent = crud.user.get(db_session, id=999999)
    assert non_existent is None


def test_get_user_by_email(db_session: Session) -> None:
    """Test retrieving a user by email via CRUD."""
    email = "getbyemail@example.com"
    
    # Create a test user directly
    user = User(
        email=email,
        hashed_password=get_password_hash("testpassword"),
        full_name="Get By Email User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Test getting the user by email
    stored_user = crud.user.get_by_email(db_session, email=email)
    assert stored_user is not None
    assert stored_user.email == email
    assert stored_user.id == user.id
    
    # Test non-existent email
    non_existent = crud.user.get_by_email(db_session, email="nonexistent@example.com")
    assert non_existent is None


def test_update_user(db_session: Session) -> None:
    """Test updating a user via CRUD."""
    # Create a test user
    user = User(
        email="update@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Update User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a new role
    role = Role(name="editor", description="Editor role")
    db_session.add(role)
    db_session.commit()
    
    # Update the user
    new_name = "Updated Name"
    new_email = "updated@example.com"
    user_update = schemas.UserUpdate(
        full_name=new_name,
        email=new_email,
        role_ids=[role.id]
    )
    updated_user = crud.user.update(db_session, db_obj=user, obj_in=user_update)
    
    assert updated_user.email == new_email
    assert updated_user.full_name == new_name
    assert updated_user.id == user.id
    
    # Verify roles were updated
    assert len(updated_user.roles) == 1
    assert updated_user.roles[0].name == "editor"


def test_update_user_password(db_session: Session) -> None:
    """Test updating a user's password via CRUD."""
    # Create a test user
    old_password = "oldpassword"
    user = User(
        email="updatepass@example.com",
        hashed_password=get_password_hash(old_password),
        full_name="Update Password User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Update the password
    new_password = "newpassword"
    user_update = schemas.UserUpdate(
        password=new_password
    )
    updated_user = crud.user.update(db_session, db_obj=user, obj_in=user_update)
    
    # Verify old password doesn't work
    assert not verify_password(old_password, updated_user.hashed_password)
    # Verify new password works
    assert verify_password(new_password, updated_user.hashed_password)


def test_delete_user(db_session: Session) -> None:
    """Test deleting a user via CRUD."""
    # Create a test user
    user = User(
        email="delete@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Delete User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    user_id = user.id
    
    # Delete the user
    deleted_user = crud.user.remove(db_session, id=user_id)
    
    # Verify the user was deleted
    assert deleted_user.id == user_id
    assert db_session.query(models.User).filter(models.User.id == user_id).first() is None


def test_get_multi(db_session: Session) -> None:
    """Test retrieving multiple users via CRUD."""
    # Create some test users
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            hashed_password=get_password_hash(f"password{i}"),
            full_name=f"User {i}",
            is_active=True
        )
        db_session.add(user)
    db_session.commit()
    
    # Test getting all users
    users = crud.user.get_multi(db_session)
    assert len(users) == 5
    
    # Test pagination with skip and limit
    users_page = crud.user.get_multi(db_session, skip=1, limit=2)
    assert len(users_page) == 2
    assert users_page[0].email == "user1@example.com"
    assert users_page[1].email == "user2@example.com"
    
    # Test with filters
    active_users = crud.user.get_multi(
        db_session,
        filter_params={"is_active": True}
    )
    assert len(active_users) == 5
    
    # Test with search
    searched_users = crud.user.get_multi(
        db_session,
        search="user1"
    )
    assert len(searched_users) == 1
    assert searched_users[0].email == "user1@example.com"


def test_add_and_remove_roles(db_session: Session) -> None:
    """Test adding and removing roles from a user."""
    # Create test roles
    role1 = Role(name="role1", description="Role 1")
    role2 = Role(name="role2", description="Role 2")
    db_session.add(role1)
    db_session.add(role2)
    db_session.commit()
    
    # Create a test user
    user = User(
        email="roleuser@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Role Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Add roles to the user
    updated_user = crud.user.add_roles(
        db_session,
        db_obj=user,
        role_ids=[role1.id, role2.id]
    )
    assert len(updated_user.roles) == 2
    assert {role.name for role in updated_user.roles} == {"role1", "role2"}
    
    # Remove a role
    updated_user = crud.user.remove_roles(
        db_session,
        db_obj=user,
        role_ids=[role1.id]
    )
    assert len(updated_user.roles) == 1
    assert updated_user.roles[0].name == "role2"
    
    # Test removing non-existent role (should be idempotent)
    updated_user = crud.user.remove_roles(
        db_session,
        db_obj=user,
        role_ids=[999]  # Non-existent role ID
    )
    assert len(updated_user.roles) == 1  # No change


def test_toggle_user_status(db_session: Session) -> None:
    """Test toggling a user's active status."""
    # Create a test user
    user = User(
        email="toggle@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Toggle User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Deactivate the user
    deactivated = crud.user.toggle_active(db_session, user_id=user.id)
    assert deactivated.is_active is False
    
    # Reactivate the user
    reactivated = crud.user.toggle_active(db_session, user_id=user.id)
    assert reactivated.is_active is True
    
    # Test with non-existent user
    non_existent = crud.user.toggle_active(db_session, user_id=999999)
    assert non_existent is None
