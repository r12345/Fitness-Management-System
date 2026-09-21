"""课程上课时间的解析与格式化。

课程表的 `start_time` 在接口文档里被描述成 `"周三 18:00"` 这种展示串，
但前端 `<input type="datetime-local">` 提交的是 `"2026-09-21 18:00:00"`。
两边都往同一个 DateTime 列里写，必须在这里统一成 datetime，
否则字符串会直接落到数据库（"周三 18:00" 根本写不进去），
读回来格式化时也会因为 `strptime` 失败抛 ValueError（表现为接口 500）。
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional

_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
_WEEKDAY_INDEX = {name: index for index, name in enumerate(_WEEKDAYS)}

# datetime-local 给出的是 2026-09-21T18:00，秒可以省略
_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
)

# 「周三 18:00」/「周三18:00」
_WEEKDAY_PATTERN = re.compile(r"^周([一二三四五六日])\s*(\d{1,2}):(\d{1,2})$")


def parse_start_time(value: "str | datetime | date | None") -> Optional[datetime]:
    """把各种写法的上课时间统一转成 datetime。

    :raises ValueError: 无法识别的格式，调用方应转成 400 而不是让它变成 500
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)

    text = str(value).strip()
    if not text:
        return None

    matched = _WEEKDAY_PATTERN.match(text)
    if matched:
        # 只有星期没有日期：落到「本周的这一天」，已经过去就顺延到下周
        weekday = _WEEKDAY_INDEX[f"周{matched.group(1)}"]
        today = datetime.now()
        target = today + timedelta(days=weekday - today.weekday())
        target = target.replace(
            hour=int(matched.group(2)), minute=int(matched.group(3)), second=0, microsecond=0
        )
        if target < today:
            target += timedelta(days=7)
        return target

    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    raise ValueError(f"无法识别的上课时间格式：{value!r}，请使用 2026-09-21 18:00:00")


def format_start_time(value: "str | datetime | None") -> Optional[str]:
    """把上课时间格式化成前端展示用的 "周X HH:MM"。"""
    if value is None:
        return None
    try:
        parsed = parse_start_time(value)
    except ValueError:
        # 库里可能残留无法解析的历史值，展示层降级为原样输出，不阻断整个列表
        return str(value)
    if parsed is None:
        return None
    return f"{_WEEKDAYS[parsed.weekday()]} {parsed.strftime('%H:%M')}"


def format_start_time_input(value: "str | datetime | None") -> Optional[str]:
    """把上课时间格式化成 ``<input type="datetime-local">`` 能回填的 "2026-09-21T18:00"。

    课程编辑表单要把原值塞回输入框，而展示串 "周三 18:00" 塞进去会让输入框变空、
    用户一保存就提交空值（后端解析失败表现为 500），所以展示串与回填串必须分开给。

    原先是 api/v1/courses.py 里的私有函数 ``_start_time_raw`` ——
    它是纯格式化、既不碰数据库也不构造响应模型，和 ``format_start_time`` 是一对，
    所以放到同一个工具模块里。
    """
    if value is None:
        return None
    try:
        parsed = parse_start_time(value)
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%dT%H:%M") if parsed else None
