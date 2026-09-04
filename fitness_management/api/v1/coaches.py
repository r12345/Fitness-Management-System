"""教练管理、排班与授课统计接口。"""
from fastapi import Depends, HTTPException
from typing import Optional

from ...core.database import get_db
from ...schemas.coach import CoachPageResponse, CoachCreate, CoachUpdate
from ...crud.coach import get_coach_page_list, create_coach_obj, update_coach_obj, delete_coach_obj, \
    get_coach_statistics_obj
from .router import coaches_router


@coaches_router.get("/", response_model=CoachPageResponse)
async def list_coaches(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    specialty: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    db = Depends(get_db)
):
    """教练分页列表 管理员接口"""
    page_data = await get_coach_page_list(
        db=db,
        keyword=keyword,
        status=status,
        specialty=specialty,
        page=page,
        page_size=page_size
    )
    return {
        "code": 0,
        "msg": "success",
        "data": page_data
    }

@coaches_router.post("/")
async def create_coach(coach: CoachCreate, db = Depends(get_db)):
    """创建教练 管理员接口"""
    coach = await create_coach_obj(db, coach)
    return {"code": 200, "msg": "创建成功", "data": coach}

@coaches_router.put("/{coach_id}")
async def update_coach(coach_id: int, coach: CoachUpdate, db = Depends(get_db)):
    """更新教练 管理员接口"""
    coach = await update_coach_obj(db, coach_id, coach)
    if coach is None:
        raise HTTPException(status_code=404, detail="教练不存在")
    return {"code": 200, "msg": "修改成功", "data": coach}


@coaches_router.delete("/{coach_id}")
async def delete_coach(coach_id: int, db = Depends(get_db)):
    """删除教练 管理员接口"""
    coach = await delete_coach_obj(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="教练不存在")
    return {"code": 200, "msg": "删除成功", "data": coach}

@coaches_router.get("/{coach_id}/statistics")
async def get_coach_statistics(coach_id: int, db = Depends(get_db)):
    """获取教练统计 管理员接口"""
    coach = await get_coach_statistics_obj(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="教练不存在")
    return {"code": 200, "msg": "success", "data": coach}









