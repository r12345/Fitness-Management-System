"""登录、Token、密码重置与个人信息模型。"""
from pydantic import BaseModel, EmailStr, Field, validator

class AuthRequest(BaseModel):
    role:str
    username:str
    password:str