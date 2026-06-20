# -*- coding: utf-8 -*-
"""
用户行为长期记忆
================
基于向量库存储用户报销行为画像，支持跨会话记忆
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .vector_store import get_vector_store
import json


class UserMemory:
    """用户行为长期记忆管理器"""

    def __init__(self):
        self._store = None
        self._profiles: Dict[int, Dict[str, Any]] = {}

    @property
    def store(self):
        if self._store is None:
            self._store = get_vector_store("user_memory")
        return self._store

    def build_profile(self, employee_id: int, expenses: list) -> Dict[str, Any]:
        """构建员工报销行为画像"""
        now = datetime.now()
        records = [e for e in expenses if e.get("applicant_id") == employee_id]

        # 时间维度统计
        r30 = [e for e in records if self._in_days(e, now, 30)]
        r90 = [e for e in records if self._in_days(e, now, 90)]

        # 费用类型偏好
        type_dist = {}
        for e in records:
            for item in e.get("detail", []):
                t = item.get("type", "OTHER")
                type_dist[t] = type_dist.get(t, 0) + 1

        # 状态统计
        status_dist = {}
        for e in records:
            status_dist[e["status"]] = status_dist.get(e["status"], 0) + 1

        # 金额统计
        amounts = [e["amount"] for e in records if e["status"] != "draft"]

        profile = {
            "employee_id": employee_id,
            "total_records": len(records),
            "total_amount": sum(e["amount"] for e in records),
            "recent_30d_count": len(r30),
            "recent_30d_amount": sum(e["amount"] for e in r30),
            "recent_90d_count": len(r90),
            "recent_90d_amount": sum(e["amount"] for e in r90),
            "type_distribution": type_dist,
            "status_distribution": status_dist,
            "avg_amount": round(sum(amounts) / len(amounts), 2) if amounts else 0,
            "max_amount": max(amounts) if amounts else 0,
            "reject_rate": round(status_dist.get("rejected", 0) / max(len(records), 1), 3),
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._profiles[employee_id] = profile

        # 存入向量库用于长期记忆
        memory_text = (
            f"员工{employee_id}报销画像：总计{len(records)}笔，总额¥{sum(e['amount'] for e in records):.0f}。"
            f"近30天{len(r30)}笔，近90天{len(r90)}笔。"
            f"驳回率{profile['reject_rate']:.1%}，平均金额¥{profile['avg_amount']:.0f}。"
            f"主要费用类型：{', '.join(type_dist.keys())}。"
        )
        try:
            self.store.add_documents(
                [memory_text],
                metadatas=[{"employee_id": employee_id, "type": "profile", "timestamp": now.isoformat()}],
                ids=[f"profile_{employee_id}_{now.strftime('%Y%m%d')}"],
            )
        except Exception:
            pass  # 向量库写入失败不阻塞主流程

        return profile

    def get_profile(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """获取员工画像（优先缓存）"""
        return self._profiles.get(employee_id)

    def search_memory(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """语义搜索用户行为记忆"""
        try:
            return self.store.search(query, top_k)
        except Exception:
            return []

    def get_risk_indicators(self, employee_id: int) -> Dict[str, Any]:
        """获取员工风险指标"""
        p = self._profiles.get(employee_id)
        if not p:
            return {"has_profile": False}

        return {
            "has_profile": True,
            "high_frequency": p["recent_30d_count"] >= 5,
            "high_reject_rate": p["reject_rate"] > 0.3,
            "amount_increasing": p["recent_30d_amount"] > p["recent_90d_amount"] / 3 * 1.5 if p["recent_90d_amount"] > 0 else False,
            "dominant_type": max(p["type_distribution"], key=p["type_distribution"].get) if p["type_distribution"] else "OTHER",
        }

    def _in_days(self, expense: Dict, now: datetime, days: int) -> bool:
        d = expense.get("exp_date", "")
        if not d:
            return False
        try:
            return (now - datetime.strptime(d, "%Y-%m-%d")).days <= days
        except ValueError:
            return False


# 全局单例
user_memory = UserMemory()
