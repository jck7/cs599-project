# -*- coding: utf-8 -*-
"""
员工报销行为长期记忆
====================
构建员工报销画像，作为风险识别的跨会话记忆
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..tools.base import get_all_expenses, find_employee


class UserBehaviorMemory:
    """员工报销行为画像（内存实现，可扩展为持久化）"""

    def __init__(self):
        self._cache: Dict[int, Dict[str, Any]] = {}

    def get_profile(self, employee_id: int) -> Dict[str, Any]:
        """获取员工报销行为画像"""
        if employee_id in self._cache:
            cached = self._cache[employee_id]
            # 缓存 5 分钟
            if (datetime.now() - cached["_updated_at"]).seconds < 300:
                return cached

        profile = self._build_profile(employee_id)
        self._cache[employee_id] = profile
        return profile

    def _build_profile(self, employee_id: int) -> Dict[str, Any]:
        """构建员工画像"""
        expenses = get_all_expenses()
        emp = find_employee(employee_id)
        records = [e for e in expenses if e["applicant_id"] == employee_id]

        now = datetime.now()

        # 近 30/90/180 天记录
        r30 = [e for e in records if self._in_days(e, now, 30)]
        r90 = [e for e in records if self._in_days(e, now, 90)]
        r180 = [e for e in records if self._in_days(e, now, 180)]

        # 状态统计
        status_dist = {}
        for e in records:
            status_dist[e["status"]] = status_dist.get(e["status"], 0) + 1

        # 费用类型偏好
        type_dist = {}
        for e in records:
            for item in e.get("detail", []):
                t = item.get("type", "OTHER")
                type_dist[t] = type_dist.get(t, 0) + 1

        # 金额统计
        amounts = [e["amount"] for e in records if e["status"] != "draft"]

        profile = {
            "employee_id": employee_id,
            "employee_name": emp["name"] if emp else "未知",
            "department": emp["dept_id"] if emp else 0,
            "level": emp["level"] if emp else "",
            "total_records": len(records),
            "total_amount": sum(e["amount"] for e in records),
            "recent_30d": {"count": len(r30), "amount": sum(e["amount"] for e in r30)},
            "recent_90d": {"count": len(r90), "amount": sum(e["amount"] for e in r90)},
            "recent_180d": {"count": len(r180), "amount": sum(e["amount"] for e in r180)},
            "status_distribution": status_dist,
            "type_distribution": type_dist,
            "avg_amount": round(sum(amounts) / len(amounts), 2) if amounts else 0,
            "max_amount": max(amounts) if amounts else 0,
            "reject_rate": round(status_dist.get("rejected", 0) / max(len(records), 1), 3),
            "_updated_at": now,
        }
        return profile

    def _in_days(self, expense: Dict, now: datetime, days: int) -> bool:
        """判断报销单是否在近 N 天内"""
        d = expense.get("exp_date", "")
        if not d:
            return False
        try:
            exp_dt = datetime.strptime(d, "%Y-%m-%d")
            return (now - exp_dt).days <= days
        except ValueError:
            return False

    def get_risk_indicators(self, employee_id: int) -> Dict[str, Any]:
        """获取员工风险指标（供风险识别 Agent 使用）"""
        p = self.get_profile(employee_id)
        indicators = {
            "high_frequency": p["recent_30d"]["count"] >= 5,
            "high_reject_rate": p["reject_rate"] > 0.3,
            "amount_trend": "increasing" if p["recent_30d"]["amount"] > p["recent_90d"]["amount"] / 3 * 1.5 else "stable",
            "dominant_type": max(p["type_distribution"], key=p["type_distribution"].get) if p["type_distribution"] else "OTHER",
        }
        return indicators


# 全局单例
behavior_memory = UserBehaviorMemory()
