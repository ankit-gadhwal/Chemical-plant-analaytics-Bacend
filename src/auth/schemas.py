from pydantic import BaseModel
from sqlmodel import Field
import uuid
from datetime import datetime
from src.db.models import UserRole
from typing import List


class UserCreateModel(BaseModel):
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    username: str = Field(max_length=8)
    email: str = Field(max_length= 40)
    password: str = Field(min_length=6)

class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    first_name: str
    last_name: str
    is_verified: bool = False
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {
        "from_attributes": True
    }


class UserSignupResponse(BaseModel):
    message: str
    user: UserModel
    
class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)

class PasswordResetRequestModel(BaseModel):
    email: str

class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str

class EmailModel(BaseModel):
    addresses: List[str]    

