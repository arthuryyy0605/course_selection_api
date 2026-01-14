from fastapi import HTTPException, status
from typing import Dict, Any
import oracledb
from course_selection_api.data_access_object.users_dao import UsersDAO
from course_selection_api.lib.auth_library.jwt import JwtToken, JWTKey
from course_selection_api.lib.auth_library.permission import Auth
from course_selection_api.schema.auth import RegisterRequest, LoginRequest


class AuthBusiness:
    """Business logic for authentication operations"""
    
    # 20 minutes in seconds
    TOKEN_EXPIRY_TIME = 20 * 60  # 1200 seconds
    
    @staticmethod
    async def register_user(conn, request: RegisterRequest) -> Dict[str, Any]:
        """Register a new consumer account"""
        try:
            # Check if user with this email already exists
            existing_user = await UsersDAO.get_user_by_email(conn, request.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists"
                )

            # Create the user
            user = await UsersDAO.create_user(
                conn,
                name=request.name,
                email=request.email,
                password=request.password,
                phone_number=request.phone_number,
                address=request.address,
                birthday=request.birthday
            )

            return {
                "user_id": str(user["user_id"]),
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "enabled": user["enabled"],
                "message": "Account created successfully. Please wait for administrator approval before logging in."
            }
        except oracledb.IntegrityError as e:
            # This catches if there's a race condition between checking and inserting
            error_str = str(e)
            if 'ORA-00001' in error_str or 'unique constraint' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email or phone number already exists"
                )
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    @staticmethod
    async def login_user(conn, request: LoginRequest) -> Dict[str, Any]:
        """Login a user and return JWT token"""
        # Find the user
        user = await UsersDAO.get_user_by_email(conn, request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect"
            )

        # Verify password
        if not await UsersDAO.verify_password(user["password_hash"], request.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect"
            )

        # Check if user account is enabled
        if not user.get("enabled", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not enabled. Please contact administrator for approval."
            )

        # Convert UUID to string before serializing to JSON
        # Set token expiry to 20 minutes
        access_token = JwtToken(key=JWTKey()).generate_token(
            claims={
                "user_id": str(user["user_id"]),  # Convert UUID to string
                "username": user["name"],
                "roles": user["role"],
                "attributes": [],
            },
            expired_time=AuthBusiness.TOKEN_EXPIRY_TIME)

        return {
            "access_token": access_token,
            "user": {
                "user_id": str(user["user_id"]),
                "email": user["email"],
                "name": user["name"],
                "role": user["role"]
            }
        }
    
    @staticmethod
    async def get_current_user_info(conn, auth: Auth) -> Dict[str, Any]:
        """Get information about the currently logged-in user"""
        user = await UsersDAO.get_user_by_id(conn, auth.user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "user_id": str(user["user_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "enabled": user["enabled"],
            "phone_number": user["phone_number"],
            "address": user["address"],
            "birthday": user["birthday"]
        }

    @staticmethod
    async def get_all_users(conn, auth: Auth, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get all users (admin only)"""
        # Check if user is admin
        if auth.user.roles != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view user list"
            )

        users = await UsersDAO.get_all_users(conn, limit, offset)
        
        return {
            "users": [
                {
                    "user_id": str(user["user_id"]),
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "enabled": user["enabled"],
                    "created_at": user["created_at"],
                    "updated_at": user["updated_at"]
                } for user in users
            ],
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    async def update_user_enabled_status(conn, auth: Auth, user_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable a user account (admin only)"""
        # Check if user is admin
        if auth.user.roles != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can modify user status"
            )

        # Cannot disable self
        if auth.user.id == user_id and not enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot disable your own account"
            )

        user = await UsersDAO.update_user_enabled_status(conn, user_id, enabled)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        action = "enabled" if enabled else "disabled"
        return {
            "user_id": str(user["user_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "enabled": user["enabled"],
            "message": f"User account has been {action} successfully"
        } 