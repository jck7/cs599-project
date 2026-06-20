# -*- coding: utf-8 -*-
"""
Supervisor 协调者 Agent
=======================
总协调 Agent，负责任务分发与结果汇总
支持跨 Agent 信息共享与结果聚合
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class SupervisorAgent:
    """
    多智能体协调者
    统一接收任务，自动分发给对应专业 Agent，汇总结果
    """

    def __init__(self):
        self._agents = {}
        self._task_history: List[Dict[str, Any]] = []

    def register_agent(self, name: str, agent_fn):
        """注册专业 Agent"""
        self._agents[name] = agent_fn

    def dispatch(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        分发任务到对应 Agent

        task_type:
          - "approval"   → 审批流水线（信息校验→预算校验→风险识别→决策）
          - "fill_help"  → 填报助手
          - "audit"      → 合规审计
          - "qa"         → 知识库问答
          - "analysis"   → 数据分析
        """
        start_time = datetime.now()
        task_id = f"task_{start_time.strftime('%Y%m%d%H%M%S')}_{hash(str(payload)) % 10000}"

        result = {"task_id": task_id, "task_type": task_type, "status": "success"}

        try:
            if task_type == "approval":
                result["data"] = self._run_approval_pipeline(payload)
            elif task_type == "fill_help":
                result["data"] = self._run_fill_help(payload)
            elif task_type == "audit":
                result["data"] = self._run_audit(payload)
            elif task_type == "qa":
                result["data"] = self._run_qa(payload)
            elif task_type == "analysis":
                result["data"] = self._run_analysis(payload)
            else:
                result["status"] = "error"
                result["message"] = f"未知任务类型: {task_type}"
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)

        elapsed = (datetime.now() - start_time).total_seconds()
        result["elapsed_seconds"] = round(elapsed, 2)
        result["timestamp"] = datetime.now().isoformat()

        self._task_history.append(result)
        return result

    def _run_approval_pipeline(self, payload: Dict) -> Dict:
        """执行审批流水线"""
        expense_id = payload.get("expense_id")
        if "approval" in self._agents:
            return self._agents["approval"](expense_id)
        return {"error": "审批 Agent 未注册"}

    def _run_fill_help(self, payload: Dict) -> Dict:
        """执行填报辅助"""
        if "fill_help" in self._agents:
            return self._agents["fill_help"](payload)
        return {"error": "填报助手 Agent 未注册"}

    def _run_audit(self, payload: Dict) -> Dict:
        """执行合规审计"""
        if "audit" in self._agents:
            return self._agents["audit"](payload)
        return {"error": "审计 Agent 未注册"}

    def _run_qa(self, payload: Dict) -> Dict:
        """执行知识库问答"""
        if "qa" in self._agents:
            return self._agents["qa"](payload)
        return {"error": "问答 Agent 未注册"}

    def _run_analysis(self, payload: Dict) -> Dict:
        """执行数据分析"""
        if "analysis" in self._agents:
            return self._agents["analysis"](payload)
        return {"error": "分析 Agent 未注册"}

    def get_task_history(self, limit: int = 20) -> List[Dict]:
        """获取任务历史"""
        return self._task_history[-limit:]

    def get_agent_status(self) -> Dict[str, Any]:
        """获取所有 Agent 状态"""
        return {
            "registered_agents": list(self._agents.keys()),
            "total_tasks": len(self._task_history),
            "recent_tasks": len([t for t in self._task_history
                                if t.get("timestamp", "") >= (datetime.now() - timedelta(hours=1)).isoformat()]),
        }


# 全局单例
from datetime import timedelta
supervisor = SupervisorAgent()
