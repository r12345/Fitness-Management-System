"""扣子（Coze）OAuth 会话隔离自检脚本。

在扣子后台建好 OAuth 应用、把三个值填进项目根目录的 .env 之后，跑一下：

    .venv/Scripts/python.exe check_coze.py

它会依次检查配置是否齐全 -> JWT 能不能签 -> 扣子认不认这个 JWT ->
两个不同用户是不是真的拿到了两个不同的令牌（= 会话隔离生效）。

任何一个环节没过，都会直接告诉你该改什么，不用去翻日志。
退出码 0 表示链路通，1 表示还没配好或被扣子拒了。
"""
import asyncio
import os
import pathlib
import sys

# Settings 的 env_file 是相对路径 ".env"，必须站在项目根目录才读得到。
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from fitness_management.core.config import settings  # noqa: E402
from fitness_management.core.coze import (  # noqa: E402
    CozeError,
    describe_missing,
    is_configured,
    issue_access_token,
    session_name_for,
    sign_jwt,
)

OK = "[OK]"
BAD = "[!!]"
WAIT = "[..]"

# 扣子返回这几句时分别是什么意思，直接替用户把错误翻译成人话。
HINTS = {
    "kid not been registred": "公钥指纹（kid）没在扣子注册 —— 回去核对 .env 里的 COZE_OAUTH_KID，"
    "必须是 OAuth 应用配置页显示的那一串，且该应用要完成授权。",
    "invalid signature": "签名校验不过 —— 私钥和 kid 不是同一对。重新下载一次 private_key.pem。",
    "invalid jwt": "JWT 格式不对 —— 检查 COZE_OAUTH_APP_ID 是否填了应用 ID（不是 bot_id）。",
    "no permission": "该 OAuth 应用没勾选对应权限 —— 在应用配置页勾选后要重新点「授权」。",
    "expired": "JWT 已过期 —— 本机系统时间可能不准，校准后重试。",
}


def line(flag, text):
    print(f"{flag} {text}")


def explain(exc: Exception) -> str:
    raw = str(exc)
    for key, hint in HINTS.items():
        if key in raw.lower():
            return f"{raw}\n      -> {hint}"
    return raw


def main() -> int:
    print("=" * 68)
    print("扣子 OAuth 会话隔离自检")
    print("=" * 68)

    line(WAIT, f"智能体 ID    : {settings.COZE_BOT_ID or '(空)'}")
    line(WAIT, f"OAuth 应用 ID: {settings.COZE_OAUTH_APP_ID or '(空)'}")
    line(WAIT, f"公钥指纹 kid : {settings.COZE_OAUTH_KID or '(空)'}")
    key_src = (
        "环境变量内联" if settings.COZE_OAUTH_PRIVATE_KEY
        else (settings.COZE_OAUTH_PRIVATE_KEY_PATH or "(空)")
    )
    if (
        not settings.COZE_OAUTH_PRIVATE_KEY
        and settings.COZE_OAUTH_PRIVATE_KEY_PATH
        and not pathlib.Path(settings.COZE_OAUTH_PRIVATE_KEY_PATH).is_absolute()
        and not (pathlib.Path(ROOT) / settings.COZE_OAUTH_PRIVATE_KEY_PATH).is_file()
    ):
        key_src += f"（文件不存在，应放在 {pathlib.Path(ROOT) / settings.COZE_OAUTH_PRIVATE_KEY_PATH}）"
    line(WAIT, f"私钥来源     : {key_src}")
    line(WAIT, f"换取地址     : {settings.COZE_TOKEN_URL}")
    print()

    if not is_configured():
        line(BAD, "配置不完整，会话隔离当前是关闭的（前端会退回公共 PAT）")
        print(f"      {describe_missing()}")
        print()
        print("  补齐办法：打开项目根目录的 .env（没有就从 .env.example 复制一份），")
        print("  把 COZE_OAUTH_APP_ID / COZE_OAUTH_KID 填上，")
        print("  再把控制台下载的 private_key.pem 放到 COZE_OAUTH_PRIVATE_KEY_PATH 指定的位置。")
        return 1

    line(OK, "三项配置齐全")

    # 第 1 步：能不能签出 JWT。私钥格式不对会在这里就炸。
    try:
        jwt_token = sign_jwt(session_name_for(1, "admin"))
        line(OK, f"JWT 签发成功（{len(jwt_token)} 字符，RS256）")
    except CozeError as exc:
        line(BAD, "JWT 签发失败")
        print(f"      {explain(exc)}")
        return 1

    # 第 2、3 步：分别以两个不同身份换令牌，比对是否真的隔离。
    # 两个账号、两种角色都测一遍 —— 隔离是按「角色 + 用户 ID」做的。
    identities = [(1, "admin"), (2, "member")]
    tokens = {}
    for uid, role in identities:
        session_name = session_name_for(uid, role)
        try:
            token, expires_in = asyncio.run(issue_access_token(session_name))
        except CozeError as exc:
            line(BAD, f"用户 {uid}（{session_name}）换取令牌失败")
            print(f"      {explain(exc)}")
            return 1
        tokens[session_name] = token
        line(OK, f"身份 {session_name} 拿到令牌："
                 f"{token[:12]}... 有效期 {expires_in}s")

    print()
    if len(set(tokens.values())) == 2:
        line(OK, "两个用户拿到的是不同的令牌 —— 会话隔离已生效")
    else:
        line(BAD, "两个用户拿到了同一个令牌，隔离没生效（检查 session_name 是否真的带进去了）")
        return 1

    print()
    line(OK, "链路已通。启动后端后，登录用户打开悬浮球即可使用；")
    print("     后端 GET /api/v1/agent/token 会按登录用户 ID 发放专属令牌。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
