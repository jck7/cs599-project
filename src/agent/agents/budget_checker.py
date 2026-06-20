# -*- coding: utf-8 -*-
"""预算与费用标准校验（纯规则，无LLM调用）"""

from typing import Dict, Any
from ..tools.budget_tools import get_department_budget, check_budget_affordable
from ..tools.rule_tools import check_expense_standard


def check_budget_and_standards(expense: Dict, applicant: Dict) -> Dict[str, Any]:
    dept_id = expense.get("dept_id", 1)
    amount = expense.get("amount", 0)

    budget_info = get_department_budget.invoke({"department_id": dept_id})
    affordable = check_budget_affordable.invoke({"department_id": dept_id, "amount": amount})

    over_std = 0
    for item in expense.get("detail", []):
        r = check_expense_standard.invoke({
            "employee_level": applicant.get("level", "P4"),
            "expense_type": item.get("type", "OTHER"),
            "amount_per_unit": float(item.get("amount", 0)),
        })
        if r.get("is_over_standard"):
            over_std += 1

    over_budget = not affordable.get("affordable", True)
    passed = not over_budget and over_std == 0

    return {
        "passed": passed,
        "message": f"预算{'不足' if over_budget else '充足'}，{over_std}项超标",
        "budget_info": budget_info,
        "over_budget": over_budget,
        "over_standard_count": over_std,
    }
