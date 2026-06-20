# -*- coding: utf-8 -*-
"""
预算查询工具
============
封装部门预算查询与校验逻辑
"""

from datetime import datetime
from langchain_core.tools import tool
from .base import find_department, get_budgets


@tool
def get_department_budget(department_id: int, year: int = 0) -> dict:
    """查询部门年度预算总额、已使用金额、剩余金额、使用率"""
    if year <= 0:
        year = datetime.now().year
    dept = find_department(department_id)
    if not dept:
        return {"error": f"部门 {department_id} 不存在"}
    budgets = get_budgets()
    b = budgets.get((department_id, year), {"total": 0, "used": 0})
    remain = b["total"] - b["used"]
    rate = round(b["used"] / b["total"] * 100, 1) if b["total"] > 0 else 0
    return {
        "department": dept["name"],
        "year": year,
        "total_budget": b["total"],
        "used_amount": round(b["used"], 2),
        "remaining": round(remain, 2),
        "usage_rate": rate,
        "is_over_budget": b["used"] > b["total"],
    }


@tool
def check_budget_affordable(department_id: int, amount: float, year: int = 0) -> dict:
    """检查部门预算是否可承担指定金额的报销"""
    if year <= 0:
        year = datetime.now().year
    budgets = get_budgets()
    b = budgets.get((department_id, year), {"total": 0, "used": 0})
    remain = b["total"] - b["used"]
    affordable = remain >= amount
    return {
        "department_id": department_id,
        "requested_amount": amount,
        "remaining_budget": round(remain, 2),
        "affordable": affordable,
        "shortfall": round(amount - remain, 2) if not affordable else 0,
        "after_approve_rate": round((b["used"] + amount) / b["total"] * 100, 1) if b["total"] > 0 else 0,
    }
