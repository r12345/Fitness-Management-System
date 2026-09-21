"""系统配置与日志相关数据库操作。"""
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fitness_management.models import SystemConfig, SystemLog, DictItem, User
from fitness_management.schemas.system import SystemConfigRequest, DictRequest
from fitness_management.utils.log_labels import log_type_label, role_label, role_options


async def get_config_system(db: AsyncSession):
    # ✅ 只执行1次SQL，一次性查询4个key
    keys = ["gym_name", "address", "business_hours", "phone"]
    query = select(SystemConfig.key, SystemConfig.value).where(SystemConfig.key.in_(keys))
    res = await db.execute(query)
    # 转为字典 {key:value}
    config_dict = {row.key: row.value for row in res.all()}

    # get获取，不存在返回空字符串，避免索引报错
    return {
        "gym_name": config_dict.get("gym_name", ""),
        "address": config_dict.get("address", ""),
        "business_hours": config_dict.get("business_hours", ""),
        "phone": config_dict.get("phone", "")
    }


async def update_config_system(system_config: SystemConfigRequest, db: AsyncSession):
    """逐项写入系统配置，返回每个 key 是否成功。

    原来只用 `update()`，key 不存在时 rowcount 为 0；而 key 列没有唯一约束，
    所以这里改为「有则改、无则插」，既能真实反映结果，也不会让后台永远保存不上。
    """
    update_data = [
        {"key": "gym_name", "value": system_config.gym_name},
        {"key": "address", "value": system_config.address},
        {"key": "business_hours", "value": system_config.business_hours},
        {"key": "phone", "value": system_config.phone},
    ]

    result: dict[str, bool] = {}
    for item in update_data:
        row = await db.scalar(select(SystemConfig).where(SystemConfig.key == item["key"]))
        if row is None:
            db.add(SystemConfig(key=item["key"], value=item["value"]))
        else:
            row.value = item["value"]
        result[item["key"]] = True

    await db.commit()
    return result


async def write_system_log(db: AsyncSession, *, log_type: str, role: str | None,
                           user: str, content: str) -> None:
    """往当前会话里加一条操作日志，**提交由调用方负责**。

    不在这里 commit 是有意的：
    - 登录接口要和「签发 Token」同一次事务（见 api/v1/auth.py）；
    - 中间件自己开独立会话，写完自己提交（见 core/operation_log.py）。
    两边共用一个写入函数，字段就不会各写各的。
    """
    db.add(SystemLog(log_type=log_type, role=role, user=user, content=content))


async def get_system_logs(log_type: str | None,
                          role: str | None,
                          user: str | None,
                          start_date: date | None,
                          end_date: date | None,
                          page: int,
                          page_size: int,
                          db: AsyncSession):
    """分页查操作日志，四个身份的历史操作都在这一张表里，靠 role 区分。

    顺手修掉三个原来的毛病：

    1. **没有排序却用 LIMIT/OFFSET**：MySQL 不保证顺序，翻到第二页可能又看到
       第一页的行、也可能整行都没出现过。按时间倒序排，管理员第一眼看到的就是最新操作。
    2. **结束日期把当天整天漏掉**：`created_at <= 2026-09-21` 是「<= 当天零点」，
       选「结束日期 = 今天」反而查不到今天任何一条。改成「次日零点之前」。
    3. **操作人只能精确匹配**：输入框叫「操作人」，输一半名字查不到东西。
       改为模糊匹配，并且账号和姓名都能搜。
    """
    conditions = []
    if log_type:
        conditions.append(SystemLog.log_type == log_type)
    if role:
        conditions.append(SystemLog.role == role)
    if user and user.strip():
        keyword = f"%{user.strip()}%"
        conditions.append(or_(SystemLog.user.like(keyword), User.name.like(keyword)))
    if start_date:
        conditions.append(SystemLog.created_at >= datetime.combine(start_date, time.min))
    if end_date:
        conditions.append(
            SystemLog.created_at < datetime.combine(end_date + timedelta(days=1), time.min)
        )

    # 姓名靠账号关联出来：日志里只存账号，账号改名也不影响历史记录的可读性
    stmt = (
        select(SystemLog, User.name)
        .outerjoin(User, User.username == SystemLog.user)
        .where(*conditions)
        .order_by(SystemLog.created_at.desc(), SystemLog.id.desc())
    )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).all()

    # 转成纯 dict：直接把 ORM 对象丢给 jsonable_encoder 会把 _sa_instance_state
    # 这类内部状态也序列化出去，而且前端拿到的字段名也不受控。
    content_list = [
        {
            "id": log.id,
            "log_type": log.log_type,
            "log_type_label": log_type_label(log.log_type),
            "role": log.role or "",
            "role_label": role_label(log.role),
            "user": log.user,
            "name": name or "",
            "content": log.content,
            "created_at": log.created_at,
        }
        for log, name in rows
    ]
    return {
        "total": total or 0,
        "content_list": content_list,
    }


async def get_log_meta(db: AsyncSession):
    """日志筛选下拉的数据源：四个身份 + 库里实际出现过的日志类型。

    类型不是写死的清单 —— 原来前端把选项写死成 login/config_edit/add/delete，
    而库里存的是 update_config/add_member/...，两边对不上，一选就查空。
    改成从数据里取，以后新增类型也不会漏。
    """
    role_counts = dict(
        (await db.execute(
            select(SystemLog.role, func.count()).group_by(SystemLog.role)
        )).all()
    )
    type_counts = (await db.execute(
        select(SystemLog.log_type, func.count()).group_by(SystemLog.log_type)
    )).all()

    types = [
        {"value": log_type, "label": log_type_label(log_type), "count": count}
        for log_type, count in type_counts
    ]
    # 条数多的排前面，常用的类型不用翻到列表底部
    types.sort(key=lambda item: (-item["count"], item["label"]))

    # 四个身份一个不少：干干净净的新库里也该能按「健身教练」筛
    roles = [
        {**option, "count": role_counts.get(option["value"], 0)}
        for option in role_options()
    ]
    return {
        "types": types,
        "roles": roles,
        "total": sum(count for _, count in type_counts),
    }


async def get_system_dicts(db: AsyncSession):
    query = select(DictItem)
    res = await db.execute(query)
    return res.scalars().all()


async def create_system_dict(dict_info:DictRequest, db: AsyncSession):
    dicts = DictItem(**dict_info.model_dump())
    db.add(dicts)
    await db.commit()
    await db.refresh(dicts)
    return dicts
