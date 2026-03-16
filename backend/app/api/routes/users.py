from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.models.connection import get_db
from app.models.database import User
from app.models.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    List all users with pagination.
    
    skip/limit pattern: This is standard pagination. skip=0, limit=10
    returns the first 10. skip=10, limit=10 returns the next 10.
    The agent won't use this directly, but it's useful for debugging.
    """
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user.
    
    Note the duplicate check: we look up by email first. This is
    a business rule — no two users can share an email. The database 
    also enforces this with a UNIQUE constraint, but checking here 
    gives us a friendly error message instead of a raw SQL error.
    """
    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_user = User(id=str(uuid.uuid4()), **user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
