"""统一响应格式与分页查询模型。"""
from collections.abc import Iterable

from pydantic import BaseModel


def to_payload(model: BaseModel) -> dict:
    """响应体统一序列化。

    必须走 ``mode="json"``：``date`` / ``datetime`` / ``Decimal`` 等类型
    直接 ``model_dump()`` 会留下 Python 对象，塞进 JSONResponse 时才报错、
    且报错位置离问题源头很远。
    """
    return model.model_dump(mode="json")


def serialize_rows(model: type[BaseModel], rows: Iterable) -> list[dict]:
    """按 schema 声明的字段序列化查询结果。

    出参形状完全由 ``model`` 决定，不随 SQL 里选了哪几列而漂移：
    crud 可以放心多查几列（例如为了排序、为了判空），多出来的列不会漏给前端。

    原先是 api/v1/coach_panel.py 里的私有函数 ``_serialize``。
    它只做「行数据 → 响应体」的纯转换、不碰数据库，属于 schema 的职责；
    放在接口层会让每个模块各写一份同样的实现。
    """
    return [to_payload(model.model_validate(row)) for row in rows]
