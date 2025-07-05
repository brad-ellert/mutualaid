# Import models here to make them available when importing from app.models
from app.models.base import Base
from app.models.user import User, Role, user_roles

# This makes these available when importing from app.models
__all__ = ["Base", "User", "Role", "user_roles"]
