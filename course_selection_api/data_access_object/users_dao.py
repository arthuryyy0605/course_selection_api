import bcrypt
from .db import Database


class UsersDAO:
    """Data Access Object for User operations"""

    @staticmethod
    async def get_user_by_email(conn, email: str):
        """Get a user by email"""
        query = """
        SELECT user_id, name, email, password_hash, role, phone_number, address, birthday, enabled
        FROM USERS 
        WHERE email = $1
        """
        return await Database.fetchrow(conn, query, email)

    @staticmethod
    async def get_user_by_id(conn, user_id: str):
        """Get a user by ID"""
        query = """
        SELECT user_id, name, email, phone_number, address, birthday, role, enabled
        FROM USERS 
        WHERE user_id = $1
        """
        return await Database.fetchrow(conn, query, user_id)

    @staticmethod
    async def create_user(conn, name: str, email: str, password: str, phone_number=None, address=None, birthday=None,
                          role="consumer", enabled=False):
        """Create a new user (disabled by default for security)"""
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = """
        INSERT INTO USERS (name, email, password_hash, phone_number, address, birthday, role, enabled)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING user_id, name, email, role, enabled
        """
        return await Database.fetchrow(
            conn,
            query,
            name,
            email,
            password_hash,
            phone_number,
            address,
            birthday,
            role,
            enabled
        )

    @staticmethod
    async def verify_password(stored_password_hash: str, password: str) -> bool:
        """Verify a password against a hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            stored_password_hash.encode('utf-8')
        )

    @staticmethod
    async def update_user_enabled_status(conn, user_id: str, enabled: bool):
        """Update user enabled status (admin only)"""
        query = """
        UPDATE USERS 
        SET enabled = $2, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = $1
        RETURNING user_id, name, email, role, enabled
        """
        return await Database.fetchrow(conn, query, user_id, enabled)

    @staticmethod
    async def get_all_users(conn, limit: int = 100, offset: int = 0):
        """Get all users with pagination (admin only)"""
        query = """
        SELECT user_id, name, email, role, enabled, created_at, updated_at
        FROM USERS 
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """
        return await Database.fetch(conn, query, limit, offset)
