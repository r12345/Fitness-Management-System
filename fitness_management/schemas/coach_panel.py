"""教练工作台相关请求/响应模型。

教练身份一律由当前登录用户（role=coach）推导，请求体不接收 coach_id。

日期类型统一以 date_type 引用 datetime.date：本模块存在名为 date 的响应字段，
若直接写 Optional[date]，字段名会遮蔽同名类型，pydantic 解析注解时会把它认成 None。
"""
from datetime import date as date_type
from datetime import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import to_payload


# ===== 请求模型 =====

class ScheduleUpdate(BaseModel):
    """修改排课请求体：日期、开始时间、结束时间、地点都可以改。

    不含 course_id —— 排课是按课程时间自动派生的，课程归属由课程表决定，
    教练要改的是「这一次课挪到哪儿、几点上」，不是把它挂到别的课程上。

    原来这里叫 ScheduleCreate（教练手填整条排课）。改成派生之后不再有手工新增，
    只保留「对已生成的那一条做调整」，所以字段一致、语义从「新建」变成「修改」。
    """
    schedule_date: date_type = Field(..., description="上课日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    location: str = Field(..., description="上课地点")

    @field_validator("location")
    @classmethod
    def _location_not_blank(cls, value: str) -> str:
        """地点必填且不能是空白串。

        原来只声明成 str，前端传 "" 也能建出一条没有地点的排课；
        前端已经改成可选可填的输入框，后端这道校验是兜底（curl 也能打进来）。
        """
        text = (value or "").strip()
        if not text:
            raise ValueError("上课地点不能为空")
        return text


class ScheduleStatusUpdate(BaseModel):
    """修改排课状态请求体。"""
    status: str = Field(..., description="目标状态：未开始 / 已签到 / 已取消")


class MyProfileUpdate(BaseModel):
    """教练自助修改个人资料。

    只放行教练自己能决定的字段：姓名、联系方式、专长。
    薪资 / 在职状态 / 累计课时 / 平均评分 **不在这里** ——
    前三者由管理员维护、评分由学员评价统计得出，给了教练改的口子，
    他就能自己涨薪、自己把状态改成「休假」、自己刷分。
    """
    name: str = Field(..., description="姓名")
    phone: str = Field(..., description="联系方式")
    specialties: str = Field(..., description="专长")

    @field_validator("name", "phone", "specialties")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """三项都是非空字段，统一 strip 后校验，避免落库一串空格。"""
        text = (value or "").strip()
        if not text:
            raise ValueError("不能为空")
        return text


# ===== 响应模型 =====

class MyScheduleItem(BaseModel):
    """我的排课项。

    排课由课程时间派生：星期几与开始时间取自课程的上课时间，结束时间 = 开始时间
    + 课程时长，地点也继承课程。教练可以针对「这一次课」改日期 / 时段 / 地点。

    status 由后端按排课时间推导：未开始 / 进行中 / 已结束；
    教练做过的动作（已签到、已取消）会覆盖自动判定。
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    coach_id: int
    course_id: int
    course_name: Optional[str] = Field(None, description="课程名称")
    duration: Optional[int] = Field(None, description="课程时长（分钟），改排课时用于自动补结束时间")
    schedule_date: Optional[date_type] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    booked_count: Optional[int] = 0
    status: Optional[str] = Field(
        None, description="排课状态：未开始 / 进行中 / 已结束 / 已签到 / 已取消（后两者为人工状态）"
    )


class MyStudentItem(BaseModel):
    """我的学员项。"""
    model_config = ConfigDict(from_attributes=True)

    member_id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    card_type: Optional[str] = None
    card_expire: Optional[date_type] = None
    status: Optional[str] = Field(None, description="会员卡状态：正常/过期/暂停")
    goal: Optional[str] = Field(None, description="训练目标")
    current_plan: Optional[str] = Field(None, description="当前训练部位")
    recent_training: Optional[date_type] = Field(None, description="最近一次到店日期")


class MyRecordItem(BaseModel):
    """授课记录项。"""
    model_config = ConfigDict(from_attributes=True)

    date: Optional[date_type] = Field(None, description="上课日期")
    course: Optional[str] = Field(None, description="课程名称")
    student: Optional[str] = Field(None, description="学员姓名")
    hours: Optional[float] = Field(None, description="课时数")
    score: Optional[float] = Field(None, description="教练评分")
    comment: Optional[str] = Field(None, description="备注")


class MyProfileItem(BaseModel):
    """教练个人资料（本人视角）。

    可改的只有 name / phone / specialties（见 MyProfileUpdate）；
    其余字段是只读展示 —— 让教练看得到自己的入职时间、在职状态、课时与评分。
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    specialties: str
    hire_date: Optional[date_type] = Field(None, description="入职时间")
    status: Optional[str] = Field(None, description="在职 / 休假 / 离职")
    hours: Optional[int] = Field(0, description="累计课时")
    score: Optional[float] = Field(None, description="平均评分")


class MemberBrief(BaseModel):
    """计划关联学员的简要信息。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

    @classmethod
    def from_member(cls, member) -> Optional["MemberBrief"]:
        """Member ORM 或已有 MemberBrief → 简要信息；传 None 原样返回 None。

        调用方拿到的学员对象来源不一致：列表里是 ORM 关系属性（``plan.member``），
        新增计划时是 crud 单独查出来的 ORM 对象，编辑计划时又是 crud 返回的 MemberBrief。
        统一在这里收口，调用方不必再判断「这次拿到的是哪种」。
        """
        if member is None:
            return None
        if isinstance(member, cls):
            return member
        return cls(id=member.id, name=member.name)


class MyPlanItem(BaseModel):
    """训练计划项。

    同时给出 member_name 与嵌套的 member：前者便于表格展示，
    后者兼容前端已使用的 item.member.id / item.member.name。
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    member_name: Optional[str] = None
    member: Optional[MemberBrief] = Field(None, description="学员简要信息，兼容前端取值")
    coach_id: int
    goal: str = Field(..., description="训练目标")
    body_part: str = Field(..., description="训练部位")
    actions: str = Field(..., description="训练动作")
    sets_reps: str = Field(..., description="组数与次数")
    frequency: str = Field(..., description="训练频率")
    start_date: date_type
    end_date: date_type
    remark: Optional[str] = None

    @classmethod
    def from_plan(cls, plan, member=None) -> dict:
        """TrainPlan ORM → 响应体字典。

        member 可以是 Member ORM、MemberBrief，或 None（取不到学员时只留 member_id）。

        原先是 api/v1/coach_panel.py 里的私有函数 ``_plan_payload``：
        它逐个字段抄 ORM 属性、不碰数据库，属于 schema 的职责。
        """
        brief = MemberBrief.from_member(member)
        return to_payload(cls(
            id=plan.id,
            member_id=plan.member_id,
            member_name=brief.name if brief else None,
            member=brief,
            coach_id=plan.coach_id,
            goal=plan.goal,
            body_part=plan.body_part,
            actions=plan.actions,
            sets_reps=plan.sets_reps,
            frequency=plan.frequency,
            start_date=plan.start_date,
            end_date=plan.end_date,
            remark=plan.remark,
        ))
