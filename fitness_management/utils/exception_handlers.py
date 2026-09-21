"""全局异常处理器：把各类异常统一压成前端可读的 ``{"detail": "..."}``。

放在 utils 下、与 res.py 相邻 —— res.py 负责「成功响应长什么样」，
这里负责「出错时返回什么」，两者合起来才是完整的响应约定。
main.py 只负责注册，不写实现。

业务异常（BizError）的处理器在 res.py 里，因为它与业务错误码的定义是一体的。
"""
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """把 pydantic 的报错压成一句中文。

    FastAPI 默认返回的 ``detail`` 是一个**数组**，前端 request.js 只接受字符串
    （``asText`` 会把它丢掉），于是所有 422 都退化成「请求失败（HTTP 422）」，
    看不出到底哪个字段错了。
    """
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(
        str(part) for part in first.get("loc", ()) if part not in ("body", "query", "path")
    )
    reason = first.get("msg", "参数不合法")
    detail = f"参数校验失败：{field} {reason}" if field else f"参数校验失败：{reason}"
    return JSONResponse(status_code=422, content={"detail": detail})


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底 500。异常堆栈照旧打到日志里，但不把内部细节吐给前端。"""
    logger.exception("未捕获异常 %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误，请稍后重试"})
