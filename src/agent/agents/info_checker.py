# -*- coding: utf-8 -*-
"""信息完整性校验（纯规则，无LLM调用）"""

from typing import Dict, Any


def check_info_completeness(expense: Dict, applicant: Dict) -> Dict[str, Any]:
    missing, warnings = [], []

    if not expense.get("title", "").strip():
        missing.append("报销标题")
    if not expense.get("amount") or expense["amount"] <= 0:
        missing.append("报销金额")
    if not expense.get("exp_date"):
        missing.append("费用日期")
    if not expense.get("detail"):
        missing.append("费用明细")

    for i, item in enumerate(expense.get("detail", []), 1):
        if not item.get("type"):
            missing.append(f"第{i}行类型")
        if not item.get("amount") or float(item.get("amount", 0)) <= 0:
            missing.append(f"第{i}行金额")

    if not expense.get("attachments"):
        warnings.append("未上传附件")

    passed = len(missing) == 0
    return {
        "passed": passed,
        "message": f"缺少{len(missing)}项" if not passed else "信息完整",
        "missing_fields": missing,
        "warnings": warnings,
    }
