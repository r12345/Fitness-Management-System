"""操作日志中间件：把四个身份的写操作自动记进 ``sys_log``。

为什么用中间件、而不是在每个接口里手写一行——

项目里有 40 个写接口、散在 13 个模块里。手写意味着每加一个接口都可能漏记，
而且「漏没漏」没人一眼看得出来。中间件只有一处，覆盖现在和将来的所有写操作。

几个刻意的取舍：

* **只记写操作**（POST/PUT/PATCH/DELETE），GET 不记。查询不改变任何数据，
  记进来只会把日志刷成流水账，真要找「谁动了东西」时反而被淹没。
* **只记成功的**（2xx）。被 400/403 拦下的请求没改到任何数据，
  记成「已操作」是误导。
* **登录在接口里单独记**（见 ``api/v1/auth.py``）。登录失败时它也返回 HTTP 200
  （响应体是 ``{"message": "密码错误或身份错误"}``），中间件只看状态码分不出成败，
  记在接口里才准。
* **写日志失败绝不影响业务请求**。整段包在 try 里，出错只留一条服务端日志。

实现上用到三个 Starlette 的细节（本仓库 Starlette 1.6 实测可用）：
``await request.body()`` 在 ``call_next`` 之前读不会影响下游解析；
``call_next`` 之后 ``request.scope["route"].path`` 是**路由模板**
（``/api/v1/coaches/{coach_id}``，不是真实路径），拿它查规则表最准；
``scope["path_params"]`` 里是解析好的路径参数。
"""
import json
import logging
from typing import Any, Optional

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from fitness_management.core.config import settings
from fitness_management.core.database import AsyncSessionLocal
from fitness_management.crud.system import write_system_log
from fitness_management.models import User

logger = logging.getLogger("uvicorn.error")

# 会被记录的方法。GET 是只读查询，不入日志
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
API_PREFIX = "/api/v1"
# 请求体超过这个大小就不读了（本项目的写接口都是小 JSON，防的是意外的大包）
MAX_BODY_BYTES = 64 * 1024

# 登录在接口里单独记，这里排除掉，免得一个动作两条记录
EXCLUDED_ROUTES = frozenset({("POST", "/api/v1/auth/login/")})

# 规则表： (HTTP 方法, 路由模板) -> (日志类型, 动作名, 从请求体里顺带记下的字段)
# 路由模板取自 FastAPI 自己登记的 path（尾斜杠要跟装饰器写法一致，如 /courses/ 与 /coaches）
ACTION_RULES: dict[tuple[str, str], tuple[str, str, tuple]] = {
    # ---- 账号与身份 ----
    ("POST", "/api/v1/auth/register"): ("create", "注册账号", ("name",)),
    ("PUT", "/api/v1/auth/password"): ("password", "修改本人登录密码", ()),

    # ---- 教练（超级管理员维护）----
    ("POST", "/api/v1/coaches"): ("create", "新增教练", ("name",)),
    ("PUT", "/api/v1/coaches/{coach_id}"): ("update", "修改教练", ("name",)),
    ("DELETE", "/api/v1/coaches/{coach_id}"): ("delete", "删除教练", ()),

    # ---- 会员（前台 / 超级管理员）----
    ("POST", "/api/v1/members/"): ("create", "新增会员", ("name",)),
    ("PUT", "/api/v1/members/{id}"): ("update", "修改会员资料", ("name",)),
    ("DELETE", "/api/v1/members/{id}"): ("delete", "删除会员", ()),
    ("PUT", "/api/v1/members/{id}/renew"): ("update", "会员续卡", ()),
    ("PUT", "/api/v1/members/{id}/status"): ("update", "修改会员状态", ("status",)),
    ("POST", "/api/v1/members/sync-status"): ("update", "同步会员卡状态", ()),

    # ---- 课程 ----
    ("POST", "/api/v1/courses/"): ("create", "新增课程", ("name",)),
    ("PUT", "/api/v1/courses/{course_id}"): ("update", "修改课程", ("name",)),
    ("DELETE", "/api/v1/courses/{course_id}"): ("delete", "删除课程", ()),
    ("POST", "/api/v1/courses/{course_id}/toggle"): ("update", "课程上下架", ("status",)),

    # ---- 预约 ----
    ("POST", "/api/v1/appointments"): ("booking", "预约课程", ("member_id",)),
    ("DELETE", "/api/v1/appointments/{appointment_id}"): ("cancel", "取消预约", ()),
    ("POST", "/api/v1/appointments/{appointment_id}/checkin"): ("checkin", "预约签到", ()),
    ("PUT", "/api/v1/appointments/{appointment_id}/resolve"): ("update", "处理预约冲突", ("status",)),

    # ---- 教练工作台 ----
    ("POST", "/api/v1/coach-panel/plans"): ("create", "新增训练计划", ("member_id",)),
    ("PUT", "/api/v1/coach-panel/plans/{plan_id}"): ("update", "修改训练计划", ()),
    ("PUT", "/api/v1/coach-panel/profile"): ("update", "修改本人教练资料", ("name",)),
    ("PUT", "/api/v1/coach-panel/schedules/{schedule_id}"): ("update", "修改排课", ("schedule_date",)),
    ("PUT", "/api/v1/coach-panel/schedules/{schedule_id}/status"): ("update", "修改排课状态", ("status",)),
    ("POST", "/api/v1/coach-panel/students"): ("update", "认领学员", ("member_id",)),

    # ---- 打卡与运动记录 ----
    ("POST", "/api/v1/training/checkin"): ("checkin", "到店打卡", ()),
    ("PUT", "/api/v1/training/checkin/{checkin_id}/leave"): ("checkin", "离店打卡", ()),
    ("POST", "/api/v1/training/records"): ("create", "新增运动记录", ("member_id",)),

    # ---- 器材 ----
    ("POST", "/api/v1/equipment"): ("create", "新增器材", ("name",)),
    ("PATCH", "/api/v1/equipment/{equipment_id}"): ("update", "修改器材", ("name",)),
    ("DELETE", "/api/v1/equipment/{equipment_id}"): ("delete", "删除器材", ()),
    ("POST", "/api/v1/equipment/{equipment_id}/maintenance"): ("create", "新增器材保养记录", ("person",)),
    ("POST", "/api/v1/equipment/{equipment_id}/repair"): ("create", "新增器材维修记录", ()),

    # ---- 会员中心（会员本人）----
    ("PUT", "/api/v1/member_center/profile"): ("update", "修改本人资料", ("name",)),

    # ---- 前台运营人员（超级管理员维护）----
    ("POST", "/api/v1/reception/staff"): ("create", "新增运营人员", ("name",)),
    ("DELETE", "/api/v1/reception/staff/{staff_id}"): ("delete", "删除运营人员", ()),
    ("DELETE", "/api/v1/reception/staff/account/{user_id}"): ("delete", "删除运营人员登录账号", ()),

    # ---- 系统配置 ----
    ("PUT", "/api/v1/system/config"): ("config", "修改系统配置", "config"),
    ("POST", "/api/v1/system/dicts"): ("create", "新增字典项", ("dict_value",)),
}

# 请求体里的外键字段 → 它指向什么，用来把「#5」写成「会员#5」
_FIELD_LABELS = {
    "member_id": "会员",
    "course_id": "课程",
    "schedule_id": "排课",
    "coach_id": "教练",
    "plan_id": "训练计划",
    "equipment_id": "器材",
    "staff_id": "运营人员",
    "user_id": "运营账号",
    "appointment_id": "预约",
    "checkin_id": "打卡记录",
}

# 系统配置只记改了哪几项（记具体值没意义，还容易把地址电话塞进日志）
_CONFIG_FIELD_LABELS = {
    "gym_name": "健身房名称",
    "address": "地址",
    "business_hours": "营业时间",
    "phone": "联系电话",
}

# 规则表没登记时的兜底词汇
_MODULE_LABELS = {
    "coaches": "教练",
    "members": "会员",
    "courses": "课程",
    "appointments": "预约",
    "equipment": "器材",
    "training": "训练",
    "consumption": "消费",
    "reception": "前台",
    "system": "系统",
    "coach-panel": "教练工作台",
    "member_center": "会员中心",
    "statistics": "统计",
    "auth": "账号",
    "dashboard": "大盘",
}
_METHOD_ACTIONS = {"POST": "新增", "PUT": "修改", "PATCH": "修改", "DELETE": "删除"}
_LOG_TYPE_BY_METHOD = {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}


class OperationLogMiddleware(BaseHTTPMiddleware):
    """拦截写操作，成功后记一条操作日志。"""

    async def dispatch(self, request: Request, call_next):
        # 先按「方法 + 前缀」粗筛：不值得记的请求连 body 都不读
        capture = (
            request.method in WRITE_METHODS
            and request.url.path.startswith(API_PREFIX)
        )
        body = await self._read_json_body(request) if capture else None

        # 业务异常交给上层异常处理器，这里不插手也不记日志
        response = await call_next(request)

        if capture and 200 <= response.status_code < 300:
            try:
                await self._record(request, body)
            except Exception:
                # 日志是旁路功能，绝不能因为它写不进去就把正常业务搞挂
                logger.exception("操作日志写入失败（本次请求不受影响）")
        return response

    @staticmethod
    async def _read_json_body(request: Request) -> Optional[dict]:
        """尽量把请求体读成 dict；读不到就返回 None，日志退化成只记动作。

        只读小体积 JSON：DELETE 之类根本没有 body，将来若加附件上传也不该整包读进内存。
        """
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            return None
        if "json" not in (request.headers.get("content-type") or "").lower():
            return None
        try:
            raw = await request.body()
        except Exception:
            return None
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    async def _record(self, request: Request, body: Optional[dict]) -> None:
        # 路由模板只有路由命中后才有；307 尾斜杠跳转、404 这些都拿不到，正好跳过
        route = request.scope.get("route")
        template = getattr(route, "path", None)
        if not template:
            return

        key = (request.method, template)
        if key in EXCLUDED_ROUTES:
            return

        log_type, label, detail = ACTION_RULES.get(key) or _fallback_action(request.method, template)
        path_params = request.scope.get("path_params") or {}

        actor = await _resolve_actor(request)
        if actor:
            username, role = actor
        else:
            # 没登录态的写操作（目前只有注册）只能从请求体里认人
            username, role = _actor_from_body(body)
        if not username:
            logger.warning("写操作无法确定操作人，未记日志：%s %s", request.method, template)
            return

        await _write_log(
            log_type=log_type,
            role=role,
            user=username,
            content=_build_content(label, detail, body or {}, path_params),
        )


async def _resolve_actor(request: Request) -> Optional[tuple[str, str]]:
    """从 Authorization 解析出操作人：(登录账号, 身份)。

    这里自己解一遍 Token，而不是去复用接口的登录依赖 —— 中间件跑在依赖之外，
    自己解能覆盖所有接口，也省得为了「顺手把当前用户传出来」去改 40 个接口的签名。
    解不出来就返回 None，由调用方决定怎么兜底。
    """
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # 和 core/security.py 同一口径：refresh token 不能当 access 用
        if payload.get("type", "access") != "access":
            return None
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        return None

    async with AsyncSessionLocal() as session:
        row = await session.get(User, user_id)
        if not row:
            return None
        return row.username, row.role


def _actor_from_body(body: Optional[dict]) -> tuple[str, Optional[str]]:
    """未登录场景下从请求体里取操作人（注册接口就是这种）。"""
    if not body:
        return "", None
    return str(body.get("username") or ""), body.get("role")


async def _write_log(*, log_type: str, role: Optional[str], user: str, content: str) -> None:
    """用独立会话写日志。

    刻意不共用请求的会话：请求会话在响应生成阶段就结束/提交了，
    借它来写要么写不进去，要么把日志卷进业务事务里一起回滚。
    """
    async with AsyncSessionLocal() as session:
        await write_system_log(
            session, log_type=log_type, role=role, user=user, content=content
        )
        await session.commit()


def _build_content(label: str, detail: Any, body: dict, path_params: dict) -> str:
    """拼操作内容，形如「修改教练：第二」「删除排课：#12」「修改系统配置：地址」。

    详情优先取请求体里的字段（有名字就记名字，人一眼看得懂）；
    取不到就退回路径参数里的编号（至少能定位到是哪一条）。
    """
    if detail == "config":
        return f"{label}：{'、'.join(_config_fields(body))}"

    parts = []
    for field in detail:
        value = body.get(field)
        if value in (None, ""):
            continue
        if field.endswith("_id"):
            # 「5」看不出是会员还是课程，补上前缀写成「会员#5」
            parts.append(f"{_FIELD_LABELS.get(field, '')}#{value}")
        else:
            parts.append(str(value))

    if not parts:
        target = _single_path_param(path_params)
        if target:
            parts.append(f"#{target}")
    if not parts:
        return label
    return f"{label}：{'、'.join(parts)}"


def _config_fields(body: dict) -> list[str]:
    """系统配置记「改了哪几项」，不记具体值。"""
    return [
        label
        for key, label in _CONFIG_FIELD_LABELS.items()
        if body.get(key) not in (None, "")
    ] or ["未提交任何配置项"]


def _single_path_param(path_params: dict) -> Optional[Any]:
    """取路径参数里的编号。

    本项目所有带参路由都只有一个路径参数（``{coach_id}`` / ``{id}`` / ``{schedule_id}``…），
    所以取唯一那个值即可；出现多个就不猜，交给调用方退化处理。
    """
    values = [value for value in path_params.values() if value not in (None, "")]
    return values[0] if len(values) == 1 else None


def _fallback_action(method: str, template: str) -> tuple[str, str, tuple]:
    """规则表里没登记的路由给个兜底描述。

    以后新增接口忘了登记规则时，日志里会出现「新增课程：瑜伽课」而不是彻底没有记录 ——
    动作和模块都还能看出来，比静默丢失强。
    """
    segments = template.strip("/").split("/")   # ['api', 'v1', 'courses', '{course_id}']
    module = segments[2] if len(segments) > 2 else ""
    module_label = _MODULE_LABELS.get(module, module or "其他")
    return (
        _LOG_TYPE_BY_METHOD.get(method, "update"),
        f"{_METHOD_ACTIONS.get(method, '操作')}{module_label}",
        (),
    )
