# -*- coding: utf-8 -*-
"""
历史报销记录工具
================
查询员工历史报销行为，供风险识别使用
"""

from datetime import datetime, timedelta
from langchain_core.tools import tool
from .base import get_all_expenses, find_employee


@tool
def get_employee_expense_history(employee_id: int, days: int = 90) -> dict:
    """查询员工近N天的报销历史记录，包括笔数、总金额、状态分布"""
    expenses = get_all_expenses()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    records = [e for e in expenses if e["applicant_id"] == employee_id and e.get("exp_date", "") >= cutoff]

    status_dist = {}
    total = 0.0
    for e in records:
        status_dist[e["status"]] = status_dist.get(e["status"], 0) + 1
        total += e["amount"]

    emp = find_employee(employee_id)
    return {
        "employee": emp["name"] if emp else f"ID:{employee_id}",
        "period_days": days,
        "total_records": len(records),
        "total_amount": round(total, 2),
        "status_distribution": status_dist,
        "avg_amount": round(total / len(records), 2) if records else 0,
        "records": [
            {"id": e["id"], "title": e["title"], "amount": e["amount"],
             "status": e["status"], "date": e["exp_date"]}
            for e in sorted(records, key=lambda x: x["exp_date"], reverse=True)[:20]
        ],
    }


@tool
def detect_frequency_anomaly(employee_id: int, days: int = 30, threshold: int = 5) -> dict:
    """检测员工近期报销频率是否异常（超过阈值）"""
    expenses = get_all_expenses()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    records = [e for e in expenses if e["applicant_id"] == employee_id
               and e.get("exp_date", "") >= cutoff and e["status"] != "draft"]

    is_anomaly = len(records) >= threshold
    return {
        "employee_id": employee_id,
        "period_days": days,
        "record_count": len(records),
        "threshold": threshold,
        "is_anomaly": is_anomaly,
        "message": f"近{days}天报销{len(records)}笔，{'超过' if is_anomaly else '未超过'}阈值{threshold}笔",
    }


@tool
def detect_amount_spike(employee_id: int, days: int = 90) -> dict:
    """检测员工近期报销金额是否有异常飙升"""
    expenses = get_all_expenses()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    records = [e for e in expenses if e["applicant_id"] == employee_id
               and e.get("exp_date", "") >= cutoff and e["status"] in ("approved", "paid")]

    if not records:
        return {"employee_id": employee_id, "has_spike": False, "message": "无历史通过记录"}

    amounts = [e["amount"] for e in records]
    avg = sum(amounts) / len(amounts)
    max_amt = max(amounts)
    # 最大值超过均值 3 倍视为异常
    has_spike = max_amt > avg * 3 and max_amt > 2000

    return {
        "employee_id": employee_id,
        "avg_amount": round(avg, 2),
        "max_amount": round(max_amt, 2),
        "has_spike": has_spike,
        "spike_ratio": round(max_amt / avg, 1) if avg > 0 else 0,
        "message": f"均值¥{avg:.0f}，最大¥{max_amt:.0f}，{'存在' if has_spike else '无'}异常飙升",
    }
