# -*- coding: utf-8 -*-
"""
报表分析工具
============
封装数据分析与报表生成能力
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.tools import tool
from .base import get_all_expenses, get_all_employees, find_department, get_budgets


@tool
def query_expense_stats(query_type: str = "dept_rank", year: int = 0, month: int = 0) -> dict:
    """
    查询报销统计数据
    query_type: dept_rank(部门排名), monthly_trend(月度趋势), type_distribution(类型分布)
    """
    if year <= 0:
        year = datetime.now().year
    expenses = get_all_expenses()
    filtered = [e for e in expenses if e.get("exp_date", "").startswith(str(year))
                and e["status"] in ("approved", "paid", "archived")]

    if month > 0:
        filtered = [e for e in filtered if int(e["exp_date"][5:7]) == month]

    if query_type == "dept_rank":
        dept_totals = {}
        for e in filtered:
            dept_totals[e["dept_id"]] = dept_totals.get(e["dept_id"], 0) + e["amount"]
        ranked = sorted(dept_totals.items(), key=lambda x: x[1], reverse=True)
        return {
            "type": "dept_rank",
            "data": [{"dept_id": did, "dept_name": (find_department(did) or {}).get("name", ""),
                       "total": round(amt, 2)} for did, amt in ranked],
        }

    elif query_type == "monthly_trend":
        monthly = {}
        for e in filtered:
            m = e["exp_date"][:7]
            monthly[m] = monthly.get(m, 0) + e["amount"]
        return {
            "type": "monthly_trend",
            "data": [{"month": m, "total": round(v, 2)} for m, v in sorted(monthly.items())],
        }

    elif query_type == "type_distribution":
        type_totals = {}
        for e in filtered:
            for item in e.get("detail", []):
                t = item.get("type", "OTHER")
                type_totals[t] = type_totals.get(t, 0) + float(item.get("amount", 0))
        return {
            "type": "type_distribution",
            "data": [{"type": t, "total": round(v, 2)} for t, v in
                     sorted(type_totals.items(), key=lambda x: x[1], reverse=True)],
        }

    return {"type": query_type, "data": [], "message": "未知查询类型"}


@tool
def detect_expense_anomalies(days: int = 30) -> dict:
    """检测近期报销异常"""
    expenses = get_all_expenses()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent = [e for e in expenses if e.get("exp_date", "") >= cutoff and e["status"] != "draft"]

    anomalies = []

    # 检测：同一人短期内多次报销
    emp_counts = {}
    for e in recent:
        eid = e["applicant_id"]
        emp_counts[eid] = emp_counts.get(eid, 0) + 1
    for eid, cnt in emp_counts.items():
        if cnt >= 5:
            anomalies.append({
                "type": "high_frequency",
                "level": "medium",
                "description": f"员工ID{eid}近{days}天报销{cnt}笔，频率偏高",
            })

    # 检测：大额单据
    for e in recent:
        if e["amount"] >= 5000:
            anomalies.append({
                "type": "large_amount",
                "level": "high",
                "description": f"报销单#{e['id']}金额¥{e['amount']:.0f}，属大额报销",
                "expense_id": e["id"],
            })

    # 检测：驳回率异常
    reject_counts = {}
    total_counts = {}
    for e in recent:
        eid = e["applicant_id"]
        total_counts[eid] = total_counts.get(eid, 0) + 1
        if e["status"] == "rejected":
            reject_counts[eid] = reject_counts.get(eid, 0) + 1
    for eid, rej in reject_counts.items():
        total = total_counts.get(eid, 1)
        if rej / total > 0.4 and total >= 3:
            anomalies.append({
                "type": "high_reject_rate",
                "level": "medium",
                "description": f"员工ID{eid}驳回率{rej}/{total}={rej/total:.0%}",
            })

    return {
        "period_days": days,
        "total_scanned": len(recent),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies[:20],
    }


@tool
def generate_monthly_report(year: int = 0, month: int = 0) -> dict:
    """生成月度运营简报"""
    if year <= 0:
        now = datetime.now()
        year, month = now.year, now.month - 1
        if month <= 0:
            year -= 1
            month = 12

    expenses = get_all_expenses()
    monthly = [e for e in expenses if e.get("exp_date", "").startswith(f"{year}-{month:02d}")]

    total = sum(e["amount"] for e in monthly)
    approved = len([e for e in monthly if e["status"] in ("approved", "paid", "archived")])
    rejected = len([e for e in monthly if e["status"] == "rejected"])
    pending = len([e for e in monthly if e["status"] == "pending"])

    # 部门排名
    dept_totals = {}
    for e in monthly:
        if e["status"] in ("approved", "paid", "archived"):
            dept_totals[e["dept_id"]] = dept_totals.get(e["dept_id"], 0) + e["amount"]
    dept_rank = sorted(dept_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "period": f"{year}-{month:02d}",
        "summary": {
            "total_records": len(monthly),
            "total_amount": round(total, 2),
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "approval_rate": round(approved / max(approved + rejected, 1) * 100, 1),
        },
        "dept_rank": [{"dept_name": (find_department(d) or {}).get("name", ""), "amount": round(a, 2)}
                       for d, a in dept_rank],
    }
