# -*- coding: utf-8 -*-
"""
报销填报助手 Agent
==================
用户填写报销单时提供实时智能辅助
"""

from typing import Dict, Any, List
from ..tools.reimbursement_tools import parse_natural_language_expense, auto_fill_suggestions
from ..tools.rule_tools import check_expense_standard
from ..tools.budget_tools import check_budget_affordable


def assist_filling(employee_id: int, employee_level: str, dept_id: int,
                   text: str = "", current_items: list = None) -> Dict[str, Any]:
    """
    填报辅助：解析自然语言 + 实时合规提示 + 智能补全

    Args:
        employee_id: 员工ID
        employee_level: 员工职级
        dept_id: 部门ID
        text: 自然语言描述（可选）
        current_items: 当前已填写的费用明细（可选）

    Returns:
        {
            "parsed": {...},           # 自然语言解析结果
            "suggestions": {...},      # 自动补全建议
            "compliance_tips": [...],  # 实时合规提示
            "budget_hint": {...},      # 预算提示
        }
    """
    result = {
        "parsed": None,
        "suggestions": None,
        "compliance_tips": [],
        "budget_hint": None,
    }

    # 1. 自然语言解析
    if text:
        try:
            parsed = parse_natural_language_expense.invoke({"text": text})
            result["parsed"] = parsed
        except Exception:
            result["parsed"] = {"title": "", "items": [], "total_amount": 0, "error": "解析失败"}

    # 2. 实时合规检查
    items = current_items or []
    if result.get("parsed") and result["parsed"].get("items"):
        items = result["parsed"]["items"]

    for item in items:
        etype = item.get("type", "OTHER")
        amount = float(item.get("amount", 0))
        try:
            check = check_expense_standard.invoke({
                "employee_level": employee_level,
                "expense_type": etype,
                "amount_per_unit": amount,
            })
            if check.get("is_over_standard"):
                result["compliance_tips"].append({
                    "type": "over_standard",
                    "level": "warning",
                    "message": check.get("message", ""),
                    "item_type": etype,
                    "limit": check.get("limit", 0),
                    "actual": amount,
                })
        except Exception:
            pass

    # 3. 预算提示
    total = sum(float(it.get("amount", 0)) for it in items)
    if total > 0:
        try:
            budget = check_budget_affordable.invoke({"department_id": dept_id, "amount": total})
            result["budget_hint"] = budget
            if not budget.get("affordable"):
                result["compliance_tips"].append({
                    "type": "over_budget",
                    "level": "error",
                    "message": f"部门预算不足，剩余¥{budget.get('remaining_budget', 0):.2f}，需¥{total:.2f}",
                })
        except Exception:
            pass

    # 4. 智能补全建议
    try:
        suggestions = auto_fill_suggestions.invoke({"employee_id": employee_id})
        result["suggestions"] = suggestions
    except Exception:
        result["suggestions"] = {"top_reasons": [], "top_types": [], "avg_amount": 0}

    return result
