"""Authentication service."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AuthenticationError
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(user_id: UUID) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """Decode JWT access token and return user_id."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user."""
    # Check if user exists
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        raise AuthenticationError("Email already registered")

    # Create user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        display_name=user_data.display_name,
        preferred_language=user_data.preferred_language,
        preferred_madhab=user_data.preferred_madhab,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Authenticate user with email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def login_user(db: AsyncSession, email: str, password: str) -> Token:
    """Login user and return token."""
    user = await authenticate_user(db, email, password)
    if not user:
        raise AuthenticationError("Invalid email or password")

    access_token = create_access_token(user.id)
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
