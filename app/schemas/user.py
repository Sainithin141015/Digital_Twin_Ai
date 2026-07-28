from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    age: Optional[int] = None
    occupation: Optional[str] = None
    goals: Optional[dict] = None
    preferences: Optional[dict] = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    age: Optional[int]
    occupation: Optional[str]
    goals: dict
    preferences: dict
