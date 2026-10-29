"""AI 助手（扣子智能体）接入接口。

只做一件事：给当前登录用户发一个**专属的**扣子访问令牌。

为什么必须在后端发：签发 JWT 要用 OAuth 应用的私钥，私钥一旦进了浏览器
就等于公开（和把 PAT 写在前端是同一个问题）。前端只拿最终结果。

拿不到（没配 OAuth）时不是报错，而是返回 ``enabled: false``，
前端会自动退回内置 PAT —— 功能照常可用，只是所有访客共用一个会话。
"""
from fastapi import Depends

from .router import agent_router
from ...core.config import settings
from ...core.coze import (
    CozeError,
    describe_missing,
    is_configured,
    issue_access_token,
    session_name_for,
)
from ...core.security import get_current_user
from ...models import User
from ...utils.res import success_response


@agent_router.get("/token")
async def get_agent_token(user: User = Depends(get_current_user)):
    """返回当前登录用户会话隔离用的扣子访问令牌。

    四种角色都放行：AI 助手是面向所有登录用户的通用入口。
    """
    if not is_configured():
        return success_response(
            msg="未启用会话隔离，已回退到公共令牌",
            data={
                "enabled": False,
                "reason": describe_missing(),
                "bot_id": settings.COZE_BOT_ID,
            },
        )

    # 身份 = 角色 + 用户 ID：每个登录账号拿到自己的 session_name，
    # 扣子就按它分开存会话 —— A 打开对话框看不到 B 说过的话。
    session_name = session_name_for(user.id, user.role)
    try:
        token, expires_in = await issue_access_token(session_name)
    except CozeError as exc:
        # 扣子侧挂了不该让整个助手不可用：如实告诉前端原因，由它决定回退
        return success_response(
            msg=str(exc),
            data={
                "enabled": False,
                "reason": str(exc),
                "bot_id": settings.COZE_BOT_ID,
                "session_name": session_name,
            },
        )

    return success_response(
        data={
            "enabled": True,
            "token": token,
            "expires_in": expires_in,
            "session_name": session_name,
            "bot_id": settings.COZE_BOT_ID,
        }
    )
