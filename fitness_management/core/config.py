"""应用配置。

支持用项目根目录下的 `.env` 覆盖任意字段（没有该文件时行为与以前完全一致）。
带默认值的字段即使不配也能启动，方便本地开发。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 允许 .env 覆盖；extra="ignore" 让 .env 里多出来的键不至于让启动失败
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str = "prod-secret-key-change-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    # 头像存储目录
    UPLOAD_DIR: str = "./uploads"

    # ---------- 扣子（Coze）AI 助手 ----------
    # 智能体 ID。默认值就是当前项目在用的那个，一般不用改。
    COZE_BOT_ID: str = "7687570944927531048"
    # OAuth 应用的 ID（JWT 的 iss），在扣子「API & SDK → 授权 → OAuth 应用」里看
    COZE_OAUTH_APP_ID: str = ""
    # OAuth 应用的公钥指纹（JWT header 的 kid），同一个页面能查到
    COZE_OAUTH_KID: str = ""
    # 私钥文件路径（控制台下载的 private_key.pem）。与下一项二选一即可。
    COZE_OAUTH_PRIVATE_KEY_PATH: str = ""
    # 也可以直接把 PEM 内容写进环境变量（适合部署时用密钥管理注入）
    COZE_OAUTH_PRIVATE_KEY: str = ""
    # 申请的 access_token 有效期上限 86399 秒（24 小时），这里默认 2 小时
    COZE_TOKEN_TTL_SECONDS: int = 7200
    # session_name 前缀，避免与同一个扣子账号下别的业务撞号
    COZE_SESSION_PREFIX: str = "gym-"
    # 用 JWT 换 access_token 的接口地址。
    # 扣子个人版与企业标准版用默认值；企业旗舰版多组织场景需要换成
    # https://api.coze.cn/api/permission/oauth2/account/{account_id}/token
    COZE_TOKEN_URL: str = "https://api.coze.cn/api/permission/oauth2/token"


settings = Settings()
