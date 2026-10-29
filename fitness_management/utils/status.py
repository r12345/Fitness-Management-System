"""预约状态常量。

`appointment.status` 在库里出现过两种写法，早期导入的那批把「待预约」当成
「已预约」的同义写法（都还没签到、都占名额）。现在语义重新定了：

  · 「已预约」= 正常预约，占用课程名额、还没签到；
  · 「待预约」= 会员在自己已经被占用的时段里又下了一单，前台还没处理冲突，
                **暂不占名额、也不能签到**，等前台在「处理冲突」里决定
                是转成「已预约」还是「已取消」。

语义一变，凡是「判重」「算已约人数」「统计待办」「前端显示哪个操作按钮」
的地方口径必须全项目一致 —— 分散内联必然漏改（历史上「已约人数少算、
行内按钮一个都不出现」就是这么来的），所以这些跨模块共用的集合集中放这里。
前端对应 `frontend/src/utils/appointmentStatus.js`，两边要一起改。
"""

from typing import Tuple

BOOKED = "已预约"
PENDING = "待预约"
CHECKED_IN = "已签到"
FINISHED = "已完成"
CANCELED = "已取消"
CONFLICT = "冲突"

# 占用课程名额：判满员、算「已约/上限」都用它。
# 「待预约」不在里面 —— 冲突还没处理，不能先占掉一个席位。
ACTIVE_STATUSES: Tuple[str, ...] = (BOOKED, CHECKED_IN)

# 还没签到，会员/前台还能取消
UNCHECKED_STATUSES: Tuple[str, ...] = (BOOKED, PENDING)

# 判重口径：冲突待处理的那单同样占着这个人的时段，否则会员能连着下好几单
CONFLICT_CHECK_STATUSES: Tuple[str, ...] = ACTIVE_STATUSES + (PENDING,)

# 前台「待处理预约」卡片：还没结课的都算待办
UNRESOLVED_STATUSES: Tuple[str, ...] = (BOOKED, PENDING)

# 「处理冲突」的入口状态：只有「待预约」需要前台介入，
# 其余状态（已预约/已签到/已完成/已取消）都不该出现这个按钮
RESOLVE_SOURCE_STATUS = PENDING

# 「处理冲突」允许落到的目标状态
RESOLVE_TARGET_STATUSES: Tuple[str, ...] = (
    BOOKED, CHECKED_IN, FINISHED, CANCELED, CONFLICT,
)

# 全部合法状态
ALL_STATUSES: Tuple[str, ...] = (
    BOOKED, PENDING, CHECKED_IN, FINISHED, CANCELED, CONFLICT,
)


def is_pending(status: str | None) -> bool:
    """是否为「时段冲突、等前台处理」的预约状态。"""
    return status == PENDING


def is_unchecked(status: str | None) -> bool:
    """是否为「还没签到」的预约状态（会员/前台还能取消）。"""
    return status in UNCHECKED_STATUSES
