"""操作日志的身份与类型词汇表。

放在 ``utils`` 下是为了让「写日志的中间件」和「读日志的接口」共用同一份常量 ——
两边各写一份中文名，改一处忘一处就会出现「筛选下拉写『超级管理员』、
表格里显示『admin』」这种对不上的情况。

身份取自 ``sys_user.role`` 的四个取值，顺序即前端下拉框的展示顺序。

日志类型分两套并存，**不是笔误**：

* 新词表（``create`` / ``update`` / ``delete`` ...）按「动作」归类，是中间件写入时用的；
* 旧词表（``add_member`` / ``update_config`` ...）是历史演示数据留下的，
  它们已经躺在库里，映射表里保留一份中文名，表格才不至于显示成一串英文键。

未知类型不报错、原样返回，免得以后新增类型忘了登记就显示空白。
"""

from typing import Dict, List, Tuple

# ===== 身份 =====

ROLE_LABELS: Dict[str, str] = {
    "admin": "超级管理员",
    "reception": "前台运营",
    "coach": "健身教练",
    "member": "普通会员",
}

# 前端下拉框与图例的顺序：按权限从高到低
ROLE_ORDER: Tuple[str, ...] = ("admin", "reception", "coach", "member")


def role_label(role: str | None) -> str:
    """身份标识转中文；历史行没有身份时返回空串（由前端显示占位符）。"""
    if not role:
        return ""
    return ROLE_LABELS.get(role, role)


# ===== 日志类型 =====

LOG_TYPE_LABELS: Dict[str, str] = {
    # 新词表：按动作归类
    "login": "登录",
    "password": "修改密码",
    "create": "新增",
    "update": "修改",
    "delete": "删除",
    "booking": "预约",
    "cancel": "取消",
    "checkin": "签到打卡",
    "config": "系统配置",
    # 旧词表：历史数据里已经在用的写法
    "add_member": "新增会员",
    "add_course": "新增课程",
    "update_course": "修改课程",
    "update_config": "修改配置",
    "delete_member": "删除会员",
}


def log_type_label(log_type: str | None) -> str:
    """日志类型转中文；没登记过的类型原样返回，不吞掉信息。"""
    if not log_type:
        return ""
    return LOG_TYPE_LABELS.get(log_type, log_type)


def role_options() -> List[dict]:
    """给前端筛选下拉用的四个身份（顺序固定，与数据里有没有记录无关）。

    四个都返回、哪怕某身份一条日志都没有 —— 下拉框不该随数据量变化，
    否则干干净净的新库里连「健身教练」这一项都找不到。
    """
    return [{"value": role, "label": ROLE_LABELS[role]} for role in ROLE_ORDER]
