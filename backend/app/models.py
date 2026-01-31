from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from enum import Enum
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    VIEWER = "VIEWER"

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: UserRole = UserRole.VIEWER

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole

class UserInDB(UserBase):
    hashed_password: str

class UserResponse(UserBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
