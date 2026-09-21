"""预约状态常量。

库里 `appointment.status` 同时存在「待预约」和「已预约」两种写法：
早期导入的 8 条历史数据是「待预约」，而 `create_appointment` 新建的记录写的是「已预约」。
两者语义完全一样（都还没签到、但都占用课程名额），所以凡是「判重」「算已约人数」
「统计待办」「前端显示操作按钮」的地方都必须同时覆盖这两个值，
否则历史数据会被当成另一种状态，导致已约人数少算、前台看不到签到/取消按钮。
"""

from typing import Tuple

# 未签到但占用名额的两个同义状态，新增/判重/统计一律以这两个为准
PENDING_STATUSES: Tuple[str, ...] = ("已预约", "待预约")

CHECKED_IN = "已签到"
FINISHED = "已完成"
CANCELED = "已取消"
CONFLICT = "冲突"

# 仍然占用课程名额的状态
ACTIVE_STATUSES: Tuple[str, ...] = PENDING_STATUSES + (CHECKED_IN,)

# 冲突处理允许落到的目标状态
RESOLVABLE_STATUSES: Tuple[str, ...] = PENDING_STATUSES + (CHECKED_IN, FINISHED, CANCELED, CONFLICT)

# 全部合法状态
ALL_STATUSES: Tuple[str, ...] = RESOLVABLE_STATUSES


def is_pending(status: str | None) -> bool:
    """是否为「未签到但占用名额」的预约状态。"""
    return status in PENDING_STATUSES
