"""Authentication router."""

from fastapi import APIRouter, HTTPException, status

from app.dependencies import Database, CurrentUser
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.services.auth import create_user, login_user
from app.core.exceptions import AuthenticationError

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Database):
    """Register a new user."""
    try:
        user = await create_user(db, user_data)
        from app.services.auth import create_access_token
        access_token = create_access_token(user.id)
        return Token(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message),
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Database):
    """Login and get access token."""
    try:
        return await login_user(db, credentials.email, credentials.password)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get current user information."""
    return UserResponse.model_validate(current_user)
