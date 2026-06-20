# -*- coding: utf-8 -*-
"""
审批规则查询工具
================
封装审批流规则、费用标准等业务规则
"""

from langchain_core.tools import tool
from .base import get_levels, get_expense_types


@tool
def get_approval_rule(amount: float) -> dict:
    """根据金额返回需要的审批流节点"""
    nodes = [
        {"node": "dept_manager", "name": "部门经理审批"},
        {"node": "finance", "name": "财务审核"},
    ]
    if amount >= 1000:
        nodes.append({"node": "finance_director", "name": "财务总监审批"})
    if amount >= 5000:
        nodes.append({"node": "ceo", "name": "总经理审批"})
    return {
        "amount": amount,
        "node_count": len(nodes),
        "nodes": nodes,
        "description": f"¥{amount:.2f} 需要 {len(nodes)} 级审批",
    }


@tool
def check_expense_standard(employee_level: str, expense_type: str, amount_per_unit: float) -> dict:
    """检查单笔费用是否超出职级标准"""
    levels = get_levels()
    lv = levels.get(employee_level, {})
    if not lv:
        return {"error": f"职级 {employee_level} 不存在"}

    type_limit_map = {
        "TRAVEL": ("travel", "差旅费/天"),
        "MEAL": ("meal", "餐饮费/餐"),
        "TRANSPORT": ("transport", "交通费/次"),
        "HOTEL": ("travel", "住宿费/天（参照差旅标准）"),
    }

    if expense_type in type_limit_map:
        key, label = type_limit_map[expense_type]
        limit = lv.get(key, 0)
        over = amount_per_unit > limit
        return {
            "level": employee_level,
            "expense_type": expense_type,
            "standard_label": label,
            "limit": limit,
            "actual": amount_per_unit,
            "is_over_standard": over,
            "over_amount": round(amount_per_unit - limit, 2) if over else 0,
            "message": f"{label}标准¥{limit}，实际¥{amount_per_unit:.2f}，{'超标' if over else '合规'}",
        }

    return {
        "level": employee_level,
        "expense_type": expense_type,
        "is_over_standard": False,
        "message": f"费用类型 {expense_type} 无明确上限标准",
    }


@tool
def get_expense_type_info() -> list:
    """获取所有费用类型及其说明"""
    types = get_expense_types()
    return [{"code": t["code"], "name": t["name"], "icon": t["icon"]} for t in types]
