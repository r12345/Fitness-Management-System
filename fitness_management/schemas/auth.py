"""登录、Token、密码重置与个人信息模型。"""
from pydantic import BaseModel, EmailStr, Field, model_validator, validator

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


class PasswordChange(BaseModel):
    """修改自己的登录密码。

    后台新增教练 / 运营人员时开的是初始账号（初始密码 123456），
    本人登录后必须能自己改掉 —— 否则所有人的密码都是公开的 123456。

    新密码要求 6 位起步：与登录页注册的口径对齐，太短等于没设。
    """
    old_password: str = Field(..., max_length=50, description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码，至少 6 位")

    @model_validator(mode="after")
    def _validate_new_password(self):
        if not self.new_password.strip():
            raise ValueError("新密码不能为空白")
        if self.new_password == self.old_password:
            raise ValueError("新密码不能与当前密码相同")
        return self

