# -*- coding: utf-8 -*-
"""
智能合规审计 Agent
==================
对全量已通过报销单进行周期性智能审计
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..tools.base import get_all_expenses, find_employee, find_department
from ..tools.history_tools import detect_frequency_anomaly, detect_amount_spike


def run_audit(days: int = 30, risk_level: str = "all") -> Dict[str, Any]:
    """
    执行合规审计扫描

    Args:
        days: 审计时间范围（天）
        risk_level: 风险等级过滤（all/low/medium/high）

    Returns:
        {
            "period_days": int,
            "total_scanned": int,
            "findings": [...],        # 审计发现
            "risk_summary": {...},    # 风险汇总
            "audit_report": str,      # 审计报告文本
        }
    """
    expenses = get_all_expenses()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    approved = [e for e in expenses if e.get("exp_date", "") >= cutoff
                and e["status"] in ("approved", "paid", "archived")]

    findings = []

    # ── 审计规则 1：拆分单据检测 ──
    # 同一员工同一日提交多笔相似金额的报销
    emp_daily = {}
    for e in approved:
        key = (e["applicant_id"], e["exp_date"])
        emp_daily.setdefault(key, []).append(e)
    for key, records in emp_daily.items():
        if len(records) >= 2:
            amounts = [r["amount"] for r in records]
            # 金额相近（差异 < 20%）
            if amounts and max(amounts) - min(amounts) < max(amounts) * 0.2:
                findings.append({
                    "type": "split_expense",
                    "level": "high",
                    "description": f"员工ID{key[0]}在{key[1]}提交{len(records)}笔相近金额报销（¥{'/'.join(f'{a:.0f}' for a in amounts)}），疑似拆分单据",
                    "employee_id": key[0],
                    "expense_ids": [r["id"] for r in records],
                    "suggestion": "建议核实是否为同一事项拆分报销",
                })

    # ── 审计规则 2：连号发票检测 ──
    # 附件文件名连续的报销单
    att_sequences = {}
    for e in approved:
        for att in e.get("attachments", []):
            # 提取附件中的数字
            import re
            nums = re.findall(r'\d+', att)
            if nums:
                base = re.sub(r'\d+', '', att)
                att_sequences.setdefault(base, []).append((int(nums[-1]), e["id"], e["applicant_id"]))
    for base, entries in att_sequences.items():
        if len(entries) >= 3:
            entries.sort()
            # 检查是否连号
            consecutive = 0
            for i in range(1, len(entries)):
                if entries[i][0] - entries[i-1][0] <= 2:
                    consecutive += 1
            if consecutive >= 2:
                findings.append({
                    "type": "sequential_invoice",
                    "level": "medium",
                    "description": f"发现{len(entries)}张疑似连号附件（{base}），涉及{len(set(e[2] for e in entries))}名员工",
                    "suggestion": "建议核实发票来源是否合规",
                })

    # ── 审计规则 3：高频报销 ──
    emp_counts = {}
    for e in approved:
        emp_counts[e["applicant_id"]] = emp_counts.get(e["applicant_id"], 0) + 1
    for eid, cnt in emp_counts.items():
        if cnt >= 8:
            emp = find_employee(eid)
            findings.append({
                "type": "high_frequency",
                "level": "medium",
                "description": f"{emp['name'] if emp else 'ID'+str(eid)}近{days}天报销{cnt}笔，频率异常偏高",
                "employee_id": eid,
                "suggestion": "建议核查报销必要性",
            })

    # ── 审计规则 4：超标报销 ──
    from ..tools.rule_tools import check_expense_standard
    from ..tools.base import get_levels
    levels = get_levels()
    for e in approved:
        emp = find_employee(e["applicant_id"])
        if not emp:
            continue
        for item in e.get("detail", []):
            try:
                check = check_expense_standard.invoke({
                    "employee_level": emp["level"],
                    "expense_type": item.get("type", "OTHER"),
                    "amount_per_unit": float(item.get("amount", 0)),
                })
                if check.get("is_over_standard"):
                    findings.append({
                        "type": "over_standard",
                        "level": "low",
                        "description": f"报销单#{e['id']}中{item.get('type')}¥{item.get('amount')}超出{emp['level']}标准",
                        "expense_id": e["id"],
                        "suggestion": "超标已审批通过，建议关注审批合规性",
                    })
            except Exception:
                pass

    # ── 审计规则 5：异常时段报销 ──
    for e in approved:
        submit = e.get("submit_time", "")
        if submit:
            try:
                dt = datetime.strptime(submit, "%Y-%m-%d %H:%M:%S")
                # 周末提交
                if dt.weekday() >= 5:
                    findings.append({
                        "type": "weekend_submit",
                        "level": "low",
                        "description": f"报销单#{e['id']}在周末提交（{submit[:10]}）",
                        "expense_id": e["id"],
                        "suggestion": "周末提交的报销单建议关注",
                    })
            except ValueError:
                pass

    # 按风险等级过滤
    if risk_level != "all":
        findings = [f for f in findings if f["level"] == risk_level]

    # 风险汇总
    risk_summary = {
        "total_findings": len(findings),
        "high": len([f for f in findings if f["level"] == "high"]),
        "medium": len([f for f in findings if f["level"] == "medium"]),
        "low": len([f for f in findings if f["level"] == "low"]),
        "by_type": {},
    }
    for f in findings:
        risk_summary["by_type"][f["type"]] = risk_summary["by_type"].get(f["type"], 0) + 1

    # 生成审计报告文本
    report_lines = [
        f"═══ 合规审计报告 ═══",
        f"审计期间：近{days}天",
        f"扫描范围：{len(approved)}笔已通过报销单",
        f"发现风险：{len(findings)}项",
        f"  高风险：{risk_summary['high']}项",
        f"  中风险：{risk_summary['medium']}项",
        f"  低风险：{risk_summary['low']}项",
        "",
        "主要发现：",
    ]
    for f in findings[:10]:
        report_lines.append(f"  [{f['level'].upper()}] {f['description']}")

    return {
        "period_days": days,
        "total_scanned": len(approved),
        "findings": findings[:50],
        "risk_summary": risk_summary,
        "audit_report": "\n".join(report_lines),
        "audit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
