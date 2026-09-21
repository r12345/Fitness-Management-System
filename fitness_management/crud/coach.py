"""教练相关数据库操作。"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Course, Appointment, Member, Schedule, TrainPlan, User
from ..models.coach import Coach
from ..schemas.coach import CoachCreate, CoachUpdate
from .user import open_login_account


async def get_coach_by_user(db: AsyncSession, user: User) -> Coach:
    """取当前登录用户对应的教练档案（教练角色专用）。

    与 ``crud/member.py: get_member_by_user`` 对称，供「按角色决定数据范围」的接口复用：
    课程写接口要判「这门课是不是我名下的」，就得先拿到当前教练的档案。
    查不到就抛 404 —— 登录账号没有教练档案。
    """
    coach = await db.scalar(select(Coach).where(Coach.user_id == user.id))
    if not coach:
        raise HTTPException(status_code=404, detail="未找到教练档案")
    return coach


async def current_coach_id_if_coach(db: AsyncSession, user: User) -> Optional[int]:
    """调用方是教练就返回他的 coach.id，其他角色返回 None。

    ``None`` 在课程写接口里的含义是「不限定归属」（管理员/前台可以管全部课程），
    所以调用方直接把它当成 ``owner_coach_id`` 往下传即可，不用各自写 if。
    """
    if user.role != "coach":
        return None
    return (await get_coach_by_user(db, user)).id


async def update_my_profile(db: AsyncSession, coach: Coach, data) -> Coach:
    """教练自助修改个人资料。

    只动姓名 / 联系方式 / 专长这三项（见 MyProfileUpdate 的说明）。
    原先教练完全改不了自己的档案：改个手机号也得找管理员 ——
    而会员在自己的个人中心里是可以改资料的，两边不对称。
    """
    coach.name = data.name
    coach.phone = data.phone
    coach.specialties = data.specialties
    await db.commit()
    await db.refresh(coach)
    return coach


async def get_coach_page_list(
    db: AsyncSession,
    keyword: Optional[str],
    status: Optional[str],
    specialty: Optional[str],
    page: int,
    page_size: int
):
    stmt = select(Coach)

    # 模糊搜索 姓名 / 手机号
    if keyword:
        stmt = stmt.where(
            (Coach.name.like(f"%{keyword}%")) |

           (Coach.phone.like(f"%{keyword}%"))
        )
    # 状态筛选
    if status:
        stmt = stmt.where(Coach.status == status)
    # 专长筛选
    if specialty:
        stmt = stmt.where(Coach.specialties.like(f"%{specialty}%"))

    # 查询总条数 (异步count)
    count_stmt = select(func.count()).select_from(stmt.subquery())  # subquery把一条已经构造好的查询语句，变成一张虚拟的临时表（子查询）。
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # 分页偏移
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    # 查询分页数据
    res = await db.execute(stmt)
    coach_records = res.scalars().all()

    item_list = []
    #  把orm模型转换为字典放进item_list
    for coach in coach_records:
        spe_arr = coach.specialties.split(",") if coach.specialties else []
        item = {
            "id": coach.id,
            "name": coach.name,
            "phone": coach.phone,
            "specialties": spe_arr,
            "status": coach.status,
            "hire_date": coach.hire_date,
            "hours": coach.hours,
            "score": coach.score
        }
        item_list.append(item)

    total_pages = (total + page_size - 1) // page_size

    page_result = {
        "items": item_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
    return page_result

# 创建教练
async def create_coach_obj(db: AsyncSession, coach_data: CoachCreate):
    """新增教练（管理员）。

    以前只往 coach 表插一条档案，「新增的教练」在 sys_user 里没有对应账号，
    拿手机号也登录不了 —— 等于加了个不能干活的教练。
    现在顺带开一个登录账号（账号=手机号，初始密码见 DEFAULT_PASSWORD），
    并且和档案同一次 commit：任一步失败就整体回滚，不会留下半截数据。
    """
    # 原来直接 return result（execute 拿到的 CursorResult），接口层把它当 data 往外吐，
    # 序列化出来是一堆内部属性。改成回读 ORM 对象。
    account, username = await open_login_account(
        db, name=coach_data.name, phone=coach_data.phone, role="coach"
    )
    coach = Coach(**coach_data.model_dump(), user_id=account.id)
    db.add(coach)
    await db.commit()
    await db.refresh(coach)
    return coach, username

# 更新教练
async def update_coach_obj(db: AsyncSession, coach_id: int, coach_data: CoachUpdate):
    stmt = select(Coach).where(Coach.id == coach_id)
    result = await db.execute(stmt)
    coach = result.scalar_one_or_none()
    if not coach:
        return None
    # 更新字段
    update_data = coach_data.model_dump(exclude_unset=True)
    stmt = update(Coach).where(Coach.id == coach_id).values(**update_data)
    await db.execute(stmt)
    await db.commit()
    new_result = await db.execute(select(Coach).where(Coach.id == coach_id))
    return new_result.scalar_one_or_none()


# 删除教练（连同名下课程一起删）
async def delete_coach_obj(db: AsyncSession, coach_id: int):
    """删除教练，并把名下课程 / 排班 / 训练计划一并删除（管理员操作）。

    以前这里是「有点数就拦」——名下还有课程就报 400，让操作者先自己结束课程。
    实际场景里教练离职就是要一次清干净，所以改成级联删除，并把删掉的规模
    回给调用方，让前端能明确告诉用户「连带删了什么」。

    删除顺序先子后父，不依赖数据库级联的隐式行为：
      appointment → coach_schedule → course → training_plan
      → member.coach_id 置空 → 登录账号 → coach

    两张表是例外，需要单独说明：
    - ``member.coach_id`` 是 ON DELETE SET NULL：学员本身保留，只是变成「未分配」，
      不会因为教练离职就把学员档案删掉。
    - ``appointment.schedule_id`` 同样是 SET NULL：只删排班的话，预约会留下来变成
      指向已删课程的空壳，所以这里按「课程 or 排班」把预约显式删掉。

    返回 ``None`` 表示教练不存在（接口层据此回 404）；成功则返回删除摘要字典。
    """
    # 原来不管教练存不存在都 return True，接口层的「教练不存在」永远走不到，
    # 删一个不存在的编号也会提示「删除成功」。先查存在性。
    coach = await db.scalar(select(Coach).where(Coach.id == coach_id))
    if not coach:
        return None

    coach_name = coach.name
    user_id = coach.user_id

    # 先摘出课程 / 排班编号：预约表要按这两列清，
    # 因为 appointment.schedule_id 的外键是 SET NULL，光删课时预约会残留下来。
    course_ids = list(
        (await db.execute(select(Course.id).where(Course.coach_id == coach_id))).scalars().all()
    )
    schedule_ids = list(
        (await db.execute(select(Schedule.id).where(Schedule.coach_id == coach_id))).scalars().all()
    )

    appointment_count = 0
    if course_ids or schedule_ids:
        conds = []
        if course_ids:
            conds.append(Appointment.course_id.in_(course_ids))
        if schedule_ids:
            conds.append(Appointment.schedule_id.in_(schedule_ids))
        cond = or_(*conds)
        appointment_count = await db.scalar(
            select(func.count(Appointment.id)).where(cond)
        ) or 0
        await db.execute(delete(Appointment).where(cond))

    # 排班要在课程之前删：排班的 course_id 是 NOT NULL，先删课会撞外键。
    await db.execute(delete(Schedule).where(Schedule.coach_id == coach_id))
    await db.execute(delete(Course).where(Course.coach_id == coach_id))

    plan_count = await db.scalar(
        select(func.count(TrainPlan.id)).where(TrainPlan.coach_id == coach_id)
    ) or 0
    await db.execute(delete(TrainPlan).where(TrainPlan.coach_id == coach_id))

    # 学员不删，只解除归属
    student_count = await db.scalar(
        select(func.count(Member.id)).where(Member.coach_id == coach_id)
    ) or 0
    if student_count:
        await db.execute(
            update(Member).where(Member.coach_id == coach_id).values(coach_id=None)
        )

    # 联动删除关联的登录账号：coach.user_id 的外键是 ON DELETE SET NULL，
    # 不主动删账号的话，sys_user 里会留下一个能登录、但每个接口都
    # 404「未找到教练档案」的孤儿账号。
    if user_id:
        account = await db.get(User, user_id)
        if account:
            await db.delete(account)

    await db.execute(delete(Coach).where(Coach.id == coach_id))
    await db.commit()

    return {
        "coach_id": coach_id,
        "name": coach_name,
        "courses": len(course_ids),
        "schedules": len(schedule_ids),
        "plans": int(plan_count),
        "students": int(student_count),
        "appointments": int(appointment_count),
    }


# 教练授课方式
async def get_coach_statistics_obj(db: AsyncSession, coach_id: int):
    # 1.读取教练基础：累计课时、平均评分（直接coach表拿）
    coach = await db.scalar(select(Coach).where(Coach.id == coach_id))
    if not coach:
        # 原来返回一份全 0 的字典，接口层的 `if coach is None` 同样是死代码，
        # 查不存在的教练会拿到 200 + 全 0，看起来像「这个教练数据是 0」。
        return None

    # 2.去重学员数量：预约过该教练课程的学员总数
    student_stmt = (
        select(func.count(Appointment.member_id.distinct()))
        .join(Course, Appointment.course_id == Course.id)
        .where(Course.coach_id == coach_id)
    )
    student_count = await db.scalar(student_stmt) or 0

    # 3.总收入：该教练所有课程价格总和
    revenue_stmt = select(func.sum(Course.price)).where(Course.coach_id == coach_id)
    revenue = await db.scalar(revenue_stmt) or 0.0

    result = {
        "coach_id": coach_id,
        "total_hours": coach.hours,
        "student_count": int(student_count),
        "average_score": round(float(coach.score), 1),
        "revenue": round(float(revenue), 2)
    }
    return result
