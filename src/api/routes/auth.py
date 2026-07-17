"""
auth.py
-------
Authentication blueprint for user registration, login, and logout.

Routes:
  POST /auth/register - Register a new user
  POST /auth/login - Login user (returns JWT token)
  POST /auth/logout - Logout user (client-side token removal)
  GET /auth/me - Get current user info (requires token)
  PUT /auth/profile - Update user profile (username/email)
  PUT /auth/password - Change user password
"""

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError, EmailStr
from sqlalchemy.exc import IntegrityError
import jwt
import os
from datetime import datetime, timedelta

from src.api.database import SessionLocal, User
from src.utils.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class RegisterRequest(BaseModel):
    """Validation schema for user registration."""

    username: str
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "Sam_mag",
                "email": "Saml@example.com",
                "password": "SecurePassword123!",
            }
        }


class LoginRequest(BaseModel):
    """Validation schema for user login."""

    username: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {"username": "Sam_mag", "password": "SecurePassword123!"}
        }


def create_jwt_token(user_id: int, username: str) -> str:
    """Create a JWT token for the user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """Extract and verify the current user from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        # Expected format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        payload = verify_jwt_token(token)
        if not payload:
            return None

        return payload
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be valid JSON"}), 400

        # Validate input
        try:
            req = RegisterRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation failed", "details": e.errors()}), 422

        # Create new user
        db = SessionLocal()
        try:
            # Check if user already exists
            existing_user = (
                db.query(User)
                .filter((User.username == req.username) | (User.email == req.email))
                .first()
            )

            if existing_user:
                return jsonify({"error": "Username or email already exists"}), 409

            # Create and save new user
            new_user = User(username=req.username, email=req.email)
            new_user.set_password(req.password)
            db.add(new_user)
            db.commit()

            # Generate JWT token
            token = create_jwt_token(new_user.id, new_user.username)

            return (
                jsonify(
                    {
                        "message": "User registered successfully. Please sign in.",
                        "user": {
                            "id": new_user.id,
                            "username": new_user.username,
                            "email": new_user.email,
                        },
                        "token": token,
                    }
                ),
                201,
            )

        except IntegrityError:
            db.rollback()
            return jsonify({"error": "Username or email already exists"}), 409
        except Exception as e:
            db.rollback()
            logger.error(f"Registration error: {e}")
            return jsonify({"error": "Registration failed"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Unexpected error in register: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user and return JWT token."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be valid JSON"}), 400

        # Validate input
        try:
            req = LoginRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation failed", "details": e.errors()}), 422

        # Find user and verify password
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == req.username).first()

            if not user or not user.check_password(req.password):
                return jsonify({"error": "Invalid username or password"}), 401

            # Generate JWT token
            token = create_jwt_token(user.id, user.username)

            return (
                jsonify(
                    {
                        "message": "Login successful",
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                        },
                        "token": token,
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({"error": "Login failed"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Unexpected error in login: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout user (client-side token removal)."""
    # JWT is stateless, so logout is handled on the client by removing the token
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/me", methods=["GET"])
def get_me():
    """Get current user info (requires valid JWT token)."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return (
            jsonify(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at.isoformat(),
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return jsonify({"error": "Failed to fetch user"}), 500
    finally:
        db.close()


# -------------------------------------------------------------------------
# NEW ROUTES – PROFILE & PASSWORD (placed OUTSIDE the get_me function)
# -------------------------------------------------------------------------


@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    """Update user profile (username and/or email)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Unauthorized"}), 401

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == current_user["user_id"]).first()
            if not user:
                return jsonify({"error": "User not found"}), 404

            new_username = data.get("username")
            new_email = data.get("email")

            if new_username:
                # Check if username already taken (by another user)
                existing = (
                    db.query(User)
                    .filter(User.username == new_username, User.id != user.id)
                    .first()
                )
                if existing:
                    return jsonify({"error": "Username already taken"}), 409
                user.username = new_username

            if new_email:
                existing = (
                    db.query(User)
                    .filter(User.email == new_email, User.id != user.id)
                    .first()
                )
                if existing:
                    return jsonify({"error": "Email already in use"}), 409
                user.email = new_email

            db.commit()
            db.refresh(user)

            return (
                jsonify(
                    {
                        "success": True,
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                        },
                    }
                ),
                200,
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Update profile error: {e}")
            return jsonify({"error": "Update failed"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Unexpected error in update_profile: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/password", methods=["PUT"])
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if not old_password or not new_password:
            return jsonify({"error": "Both old and new password are required"}), 400

        if len(new_password) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Unauthorized"}), 401

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == current_user["user_id"]).first()
            if not user:
                return jsonify({"error": "User not found"}), 404

            if not user.check_password(old_password):
                return jsonify({"error": "Invalid current password"}), 401

            user.set_password(new_password)
            db.commit()
            return (
                jsonify({"success": True, "message": "Password updated successfully"}),
                200,
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Change password error: {e}")
            return jsonify({"error": "Password change failed"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Unexpected error in change_password: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Auth blueprint is alive!"}), 200
