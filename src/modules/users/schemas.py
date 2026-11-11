import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    rol: Literal["ADMIN", "EJECUTIVO"] = "EJECUTIVO"
    activo: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=120)
    email: EmailStr | None = None
    rol: Literal["ADMIN", "EJECUTIVO"] | None = None
    activo: bool | None = None
    password: str | None = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
