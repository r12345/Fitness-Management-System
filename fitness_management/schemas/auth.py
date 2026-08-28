"""登录、Token、密码重置与个人信息模型。"""
from pydantic import BaseModel, EmailStr, Field, validator

class AuthRequest(BaseModel):
    role:str
    username:str
    password:str


class UserInfoRequest(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=50)
    role: str = Field(..., max_length=50)
    name:str = Field(..., max_length=50)
    phone: str = Field(..., max_length=50)
    status:str = Field(..., max_length=50)

