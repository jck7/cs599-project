# -*- coding: utf-8 -*-
"""
报销单操作工具
==============
封装报销单的创建、查询、修改等操作
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.tools import tool
from .base import get_all_expenses, find_employee, find_department


@tool
def parse_natural_language_expense(text: str) -> dict:
    """
    将自然语言描述转换为报销单结构化数据
    示例输入：'上周去上海出差，高铁票860，酒店两晚1200'
    """
    import re

    result = {
        "title": "",
        "items": [],
        "total_amount": 0,
        "parsed_from": text,
    }

    # 提取金额
    amounts = re.findall(r'(\d+(?:\.\d+)?)\s*(?:元|块|¥)?', text)
    amounts = [float(a) for a in amounts]

    # 提取费用类型关键词
    type_map = {
        "高铁": ("TRAVEL", "差旅费"),
        "火车": ("TRAVEL", "差旅费"),
        "机票": ("TRAVEL", "差旅费"),
        "飞机": ("TRAVEL", "差旅费"),
        "出差": ("TRAVEL", "差旅费"),
        "酒店": ("HOTEL", "住宿费"),
        "住宿": ("HOTEL", "住宿费"),
        "出租": ("TRANSPORT", "交通费"),
        "打车": ("TRANSPORT", "交通费"),
        "滴滴": ("TRANSPORT", "交通费"),
        "吃饭": ("MEAL", "餐饮费"),
        "餐": ("MEAL", "餐饮费"),
        "聚餐": ("MEAL", "餐饮费"),
        "招待": ("ENTERTAIN", "招待费"),
        "培训": ("TRAINING", "培训费"),
        "办公": ("OFFICE", "办公费"),
        "打印": ("OFFICE", "办公费"),
    }

    detected_type = ("OTHER", "其他费用")
    for kw, tp in type_map.items():
        if kw in text:
            detected_type = tp
            break

    # 提取地点
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "重庆"]
    city = ""
    for c in cities:
        if c in text:
            city = c
            break

    # 构建费用明细
    if amounts:
        for i, amt in enumerate(amounts):
            reason = text.split("，")[0] if "，" in text else text[:20]
            result["items"].append({
                "type": detected_type[0],
                "amount": amt,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "reason": f"{city + '出差' if city else ''}{detected_type[1]}",
            })
        result["total_amount"] = sum(amounts)
        result["title"] = f"{city + '出差' if city else ''}{detected_type[1]}报销"
    else:
        result["title"] = "报销申请"

    return result


@tool
def get_expense_summary(employee_id: int, year: int = 0) -> dict:
    """获取员工年度报销汇总"""
    if year <= 0:
        year = datetime.now().year
    expenses = get_all_expenses()
    records = [e for e in expenses if e["applicant_id"] == employee_id
               and e.get("exp_date", "").startswith(str(year))]

    total = sum(e["amount"] for e in records)
    by_status = {}
    by_type = {}
    for e in records:
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
        for item in e.get("detail", []):
            t = item.get("type", "OTHER")
            by_type[t] = by_type.get(t, 0) + float(item.get("amount", 0))

    return {
        "employee_id": employee_id,
        "year": year,
        "total_records": len(records),
        "total_amount": round(total, 2),
        "by_status": by_status,
        "by_type": {k: round(v, 2) for k, v in by_type.items()},
    }


@tool
def auto_fill_suggestions(employee_id: int) -> dict:
    """根据员工历史报销习惯，提供自动补全建议"""
    expenses = get_all_expenses()
    records = [e for e in expenses if e["applicant_id"] == employee_id]

    if not records:
        return {"suggestions": [], "message": "无历史记录"}

    # 常用事由
    reasons = {}
    for e in records:
        r = e.get("title", "")
        reasons[r] = reasons.get(r, 0) + 1
    top_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]

    # 常用费用类型
    types = {}
    for e in records:
        for item in e.get("detail", []):
            t = item.get("type", "OTHER")
            types[t] = types.get(t, 0) + 1
    top_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:3]

    # 平均金额
    amounts = [e["amount"] for e in records if e["status"] != "draft"]

    return {
        "top_reasons": [r[0] for r in top_reasons],
        "top_types": [t[0] for t in top_types],
        "avg_amount": round(sum(amounts) / len(amounts), 2) if amounts else 0,
        "suggestions": [
            {"field": "title", "values": [r[0] for r in top_reasons[:3]]},
            {"field": "type", "values": [t[0] for t in top_types[:2]]},
        ],
    }
