"""扣子（Coze）OAuth JWT 鉴权 —— 实现「会话隔离」的唯一官方途径。


为什么需要这个模块
------------------
扣子把**访问密钥本身**当作使用者身份。前端直接用写死的 PAT 去鉴权时，
所有访客在扣子眼里是同一个人，于是共享同一份会话记录：

    Chat SDK 启动时会先调
        GET /v1/conversations?bot_id=..&connector_id=999&sort_field=updated_at&page_num=1&page_size=1
    取「最近更新的那一条」会话，然后所有请求都打在这个 conversation_id 上。
    结果就是 B 一打开对话框，就能看到 A 刚说过的话。

官方文档「如何实现会话隔离」明确写了：会话隔离**仅 OAuth JWT 鉴权支持**，
需要在签署 JWT 时于 payload 里带上 ``session_name``（业务侧用户的唯一标识）。
官方 FAQ 还特别说明：**即使设置了 userInfo 参数也无效**（已实测确认）。


流程
----
1. 用 OAuth 应用的私钥签一个 RS256 JWT，payload 里带 ``session_name``；
2. 用这个 JWT 去换 access_token（``czs_`` 开头，有效期可指定）；
3. 前端把这个 access_token 作为 Chat SDK 的 ``auth.token``。

私钥绝不能进浏览器，所以第 1、2 步都在后端做，前端只调 :mod:`api.v1.agent` 取结果。
"""
import asyncio
import json
import logging
import pathlib
import secrets
import time
import urllib.error
import urllib.request

from jose import jwt

from .config import settings

logger = logging.getLogger(__name__)

GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"
# 扣子侧规定 JWT 自身的有效期不需要很长，10 分钟足够走完换取流程
JWT_TTL_SECONDS = 600

# session_name -> (access_token, 过期时间戳)
_cache: dict[str, tuple[str, float]] = {}


class CozeError(RuntimeError):
    """扣子侧调用失败，或本地凭据没配好。"""


def is_configured() -> bool:
    """OAuth 三件套是否齐了。缺任意一项就只能退回 PAT（= 会话不隔离）。"""
    has_key = bool(settings.COZE_OAUTH_PRIVATE_KEY) or bool(settings.COZE_OAUTH_PRIVATE_KEY_PATH)
    return bool(settings.COZE_OAUTH_APP_ID and settings.COZE_OAUTH_KID and has_key)


def describe_missing() -> str:
    """给前端/日志看的缺失项说明。"""
    missing = []
    if not settings.COZE_OAUTH_APP_ID:
        missing.append("COZE_OAUTH_APP_ID")
    if not settings.COZE_OAUTH_KID:
        missing.append("COZE_OAUTH_KID")
    if not (settings.COZE_OAUTH_PRIVATE_KEY or settings.COZE_OAUTH_PRIVATE_KEY_PATH):
        missing.append("COZE_OAUTH_PRIVATE_KEY_PATH")
    if not missing:
        return ""
    return "未配置扣子 OAuth 凭据：" + "、".join(missing)


def session_name_for(user_id: int) -> str:
    """业务侧用户标识。同一个用户永远得到同一个 session_name，才能延续自己的会话。"""
    return f"{settings.COZE_SESSION_PREFIX}{user_id}"


def _load_private_key() -> str:
    if settings.COZE_OAUTH_PRIVATE_KEY:
        return settings.COZE_OAUTH_PRIVATE_KEY.strip()

    path = pathlib.Path(settings.COZE_OAUTH_PRIVATE_KEY_PATH)
    if not path.is_absolute():
        # 相对路径按项目根目录解释，避免受启动时工作目录影响
        path = pathlib.Path(__file__).resolve().parents[2] / path
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise CozeError(f"读取扣子私钥失败：{path}（{exc}）") from exc


def sign_jwt(session_name: str) -> str:
    """签一个带 session_name 的 RS256 JWT。"""
    now = int(time.time())
    payload = {
        "iss": settings.COZE_OAUTH_APP_ID,
        "aud": "api.coze.cn",
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
        # 防重放，每次都要不一样，建议 32 字节以上
        "jti": secrets.token_urlsafe(32),
        "session_name": session_name,
    }
    headers = {"kid": settings.COZE_OAUTH_KID}
    try:
        return jwt.encode(payload, _load_private_key(), algorithm="RS256", headers=headers)
    except CozeError:
        raise
    except Exception as exc:  # 私钥格式不对、算法不支持等
        raise CozeError(f"签署扣子 JWT 失败：{exc}") from exc


def _exchange_access_token(jwt_token: str) -> dict:
    """同步换 token（放在线程里跑，别阻塞事件循环）。"""
    body = json.dumps(
        {"duration_seconds": settings.COZE_TOKEN_TTL_SECONDS, "grant_type": GRANT_TYPE}
    ).encode()
    request = urllib.request.Request(
        # 个人版/企业标准版用默认地址；企业旗舰版多组织场景可在 .env 里覆盖
        # COZE_TOKEN_URL=.../api/permission/oauth2/account/{account_id}/token
        settings.COZE_TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise CozeError(f"扣子换取 access_token 失败（HTTP {exc.code}）：{detail}") from exc
    except Exception as exc:
        raise CozeError(f"扣子换取 access_token 失败：{exc}") from exc


async def issue_access_token(session_name: str) -> tuple[str, int]:
    """取（或复用）某个 session_name 的 access_token。

    :returns: ``(access_token, 剩余有效秒数)``
    """
    if not is_configured():
        raise CozeError(describe_missing())

    cached = _cache.get(session_name)
    now = time.time()
    if cached and cached[1] - now > 120:  # 留 2 分钟余量，避免边界上拿到刚过期的
        return cached[0], int(cached[1] - now)

    data = await asyncio.to_thread(_exchange_access_token, sign_jwt(session_name))
    token = data.get("access_token")
    if not token:
        raise CozeError(f"扣子未返回 access_token：{str(data)[:200]}")

    # expires_in 是「过期时间戳」而不是「剩余秒数」，两种都兼容一下
    expires_in = data.get("expires_in")
    expires_at = float(expires_in) if expires_in and float(expires_in) > now else now + settings.COZE_TOKEN_TTL_SECONDS

    _cache[session_name] = (token, expires_at)
    logger.info("已为 session_name=%s 签发扣子访问令牌，剩余 %ds", session_name, int(expires_at - now))
    return token, int(expires_at - now)


def clear_cache() -> None:
    """配置变更后手动清缓存（测试用）。"""
    _cache.clear()
