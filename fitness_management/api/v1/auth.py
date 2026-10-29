"""登录、退出、密码重置与个人信息接口。"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.crud.user import check_user_exists, register_user, login_user, get_role_id, \
    change_password
from fitness_management.crud.system import write_system_log
from fitness_management.models import User
from fitness_management.schemas.auth import AuthRequest, PasswordChange, UserInfoRequest
from fitness_management.utils.log_labels import role_label

from .router import user_router
from ...core.database import get_db
from ...core.security import create_access_token, get_current_user
from ...utils.res import success_response


@user_router.post('/login/')
async def login(user_info:AuthRequest,db=Depends(get_db)):
    # 检查用户是否存在
    flag1 = await check_user_exists(user_info.username, db)

    if flag1 is False:
        return {"message": "用户不存在"}
    # 登录用户
    user = await login_user(user_info, db)
    if user is None:
        return {"message": "密码错误或身份错误"}
    token = create_access_token(subject=str(user.id))
    role_id = await get_role_id(user, db)
    # 登录也要进操作日志。记在这里而不是中间件里，是因为登录失败时本接口同样返回
    # HTTP 200（响应体是 {"message": "..."}），中间件只看状态码分不出成败，
    # 在这里记才知道「确实是登进来了」。四个身份的登录都会落到同一条路径上。
    await write_system_log(
        db,
        log_type="login",
        role=user.role,
        user=user.username,
        content=f"{role_label(user.role)}【{user.name}】登录系统",
    )
    await db.commit()
    return success_response(msg='success',data={
        'token': token,
        'role':user.role,
        'role_id':role_id,
        'role_name': user.name,
        'home':'/dashboard',
        'user_id':user.id,
    })


@user_router.post('/register')
async def register(user_info: UserInfoRequest,db=Depends(get_db)):
    #  检查用户是否存在
    flag1=await check_user_exists(user_info.username, db)
    if flag1 is True:
        return {"message": "用户已存在"}
    # 注册用户
    user = await register_user(user_info, db)
    if user:
        return {"message": "注册成功"}
    return {"message": "注册失败"}


# ===== 修改自己的登录密码 =====

@user_router.put('/password')
async def change_my_password(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """四个身份通用：改自己的密码。

    管理员在后台新增教练 / 运营人员时，开的是初始账号（初始密码 123456），
    本人登录后在这里改成只有自己知道的密码 —— 这条路径不区分角色，
    谁登录就改谁的，请求体里也没有「改谁」的字段，改不到别人头上。
    """
    await change_password(db, user, data.old_password, data.new_password)
    return success_response(msg="密码已修改，下次登录请使用新密码")


