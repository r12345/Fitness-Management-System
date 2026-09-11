"""统一响应格式与业务异常。

所有接口遵循文档 §2.3 的统一响应结构：

    成功：{"code": 0, "msg": "success", "data": ...}
    失败：{"code": 400, "msg": "参数错误", "data": null}

业务校验失败统一抛出 :class:`BizError`，由 ``main.py`` 注册的异常处理器
转换为统一响应，避免每个接口都写一遍错误分支。
"""
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


class BizError(Exception):
    """业务异常。

    :param msg: 提示信息（返回给前端）
    :param code: 业务错误码，见文档 §2.6；未定义的场景可直接用 HTTP 状态码
    :param status_code: HTTP 状态码
    :param data: 附加数据，一般为 None
    """

    def __init__(self, msg: str, code: int = 400, status_code: int = 400, data=None):
        self.msg = msg
        self.code = code
        self.status_code = status_code
        self.data = data
        super().__init__(msg)


def success_response(msg: str = "success", data=None) -> JSONResponse:
    """构造统一成功响应。"""
    content = {
        "code": 0,
        "msg": msg,
        "data": data,
    }
    # 目标：把任何的 FastAPI、Pydantic、ORM 对象 都要正常响应 → code、message、data
    return JSONResponse(content=jsonable_encoder(content))


def error_response(msg: str = "参数错误", code: int = 400, data=None, status_code: int = 400) -> JSONResponse:
    """构造统一失败响应。"""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"code": code, "msg": msg, "data": data}),
    )


async def biz_error_handler(request: Request, exc: BizError) -> JSONResponse:
    """BizError 全局异常处理器，保证业务错误也走统一响应格式。"""
    return error_response(msg=exc.msg, code=exc.code, data=exc.data, status_code=exc.status_code)
