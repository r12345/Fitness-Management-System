"""统一响应中的 ``code`` 取值（接口文档 §2.5 / §2.6）。

成功响应的 ``code`` 固定为 :data:`SUCCESS`；失败响应的 ``code`` 有两种来源：

* 文档 §2.6 定义了专门的业务错误码（如会员不存在、排班冲突），优先使用；
* 其余场景沿用 HTTP 状态码作为 ``code``（见 §2.5），本模块用 ``HTTP_*`` 前缀的常量表示。

新增业务错误码时，请同步更新接口文档 §2.6 的表格。
"""

# ===== 成功 =====
SUCCESS = 0

# ===== 沿用 HTTP 状态码（文档 §2.5）=====
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500

# ===== 业务错误码（文档 §2.6）=====

# 认证与权限 1001-1099
AUTH_BAD_CREDENTIALS = 1001  # 账号或密码错误
AUTH_INVALID_TOKEN = 1002  # Token 无效或过期
PERMISSION_DENIED = 1003  # 无权限访问

# 会员 2001-2099
MEMBER_NOT_FOUND = 2001  # 会员不存在
MEMBER_PHONE_EXISTS = 2002  # 会员手机号已存在
MEMBER_CARD_CANCELED = 2003  # 会员卡已注销

# 教练 3001-3099
COACH_NOT_FOUND = 3001  # 教练不存在
COACH_SCHEDULE_CONFLICT = 3002  # 教练排班冲突

# 课程与预约 4001-4099
COURSE_NOT_FOUND = 4001  # 课程不存在
COURSE_FULL = 4002  # 课程已满员
APPOINTMENT_DUPLICATED = 4003  # 同一时段重复预约

# 器材与报修 5001-5099
EQUIPMENT_NOT_FOUND = 5001  # 器材不存在
REPAIR_NOT_FOUND = 5002  # 报修记录不存在

# 统计 6001-6099
STATISTICS_BAD_PARAM = 6001  # 数据统计参数错误
