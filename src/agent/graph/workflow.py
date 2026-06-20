# -*- coding: utf-8 -*-
"""
审批工作流（极致性能版）
========================
三通道自动路由：
  极速通道（<1000元无违规）：1次LLM调用
  标准通道（1000-5000元）：2次LLM调用（并行校验+合并决策）
  严格通道（>5000元或高风险）：完整链路

文件路径：src/agent/graph/workflow.py
"""

import logging
from typing import Dict, Any
from ..config import AgentConfig

logger = logging.getLogger(__name__)


def build_workflow():
    """构建工作流（返回可调用对象）"""
    return SimpleWorkflow()


class SimpleWorkflow:
    """三通道审批工作流"""

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        expense = state["expense_data"]
        applicant = state["applicant_data"]
        amount = expense.get("amount", 0)

        # 硬规则前置：金额分级路由（代码直接判断，不走LLM）
        has_history_violation = self._check_history_violation(applicant)
        is_fast = amount < 1000 and not has_history_violation
        is_standard = 1000 <= amount < 5000 and not has_history_violation

        if is_fast:
            logger.info("[WF] Fast channel: amount=%.0f", amount)
            return self._fast_channel(state)
        elif is_standard:
            logger.info("[WF] Standard channel: amount=%.0f", amount)
            return self._standard_channel(state)
        else:
            logger.info("[WF] Strict channel: amount=%.0f", amount)
            return self._strict_channel(state)

    def _fast_channel(self, state: Dict) -> Dict:
        """极速通道：信息+预算+决策合并为1次LLM调用"""
        from ..agents.info_checker import check_info_completeness
        from ..agents.budget_checker import check_budget_and_standards

        expense = state["expense_data"]
        applicant = state["applicant_data"]

        # 硬规则校验（纯代码，不走LLM）
        info = check_info_completeness(expense, applicant)
        budget = check_budget_and_standards(expense, applicant)

        # 快速决策（1次LLM调用）
        from ..agents.decision_maker import fast_decision
        decision = fast_decision(expense, applicant, info, budget)

        state["info_check"] = info
        state["budget_check"] = budget
        state["risk_analysis"] = {"risk_score": 10, "risk_level": "low", "risk_items": []}
        state["final_decision"] = decision
        state["current_step"] = "completed"
        state["processing_log"] = [
            {"step": "fast_check", "message": "极速通道：信息+预算校验完成"},
            {"step": "fast_decision", "message": f"决策：{decision['conclusion']}"},
        ]
        return state

    def _standard_channel(self, state: Dict) -> Dict:
        """标准通道：并行校验 + 合并决策（2次LLM调用）"""
        from ..agents.info_checker import check_info_completeness
        from ..agents.budget_checker import check_budget_and_standards
        from ..agents.risk_analyzer import analyze_risk
        from ..agents.decision_maker import make_decision

        expense = state["expense_data"]
        applicant = state["applicant_data"]

        # 并行：信息校验 + 预算校验（纯代码，无LLM依赖）
        info = check_info_completeness(expense, applicant)
        budget = check_budget_and_standards(expense, applicant)

        # 风险分析（1次LLM调用）
        risk = analyze_risk(expense, applicant)

        # 综合决策（1次LLM调用）
        decision = make_decision(expense, applicant, info, budget, risk)

        state["info_check"] = info
        state["budget_check"] = budget
        state["risk_analysis"] = risk
        state["final_decision"] = decision
        state["risk_score"] = risk.get("risk_score", 0)
        state["current_step"] = "completed"
        state["processing_log"] = [
            {"step": "parallel_check", "message": "信息+预算并行校验完成"},
            {"step": "risk_analysis", "message": f"风险评分：{risk.get('risk_score', 0)}"},
            {"step": "decision", "message": f"决策：{decision['conclusion']}"},
        ]
        return state

    def _strict_channel(self, state: Dict) -> Dict:
        """严格通道：完整4节点链路"""
        from ..agents.info_checker import check_info_completeness
        from ..agents.budget_checker import check_budget_and_standards
        from ..agents.risk_analyzer import analyze_risk
        from ..agents.decision_maker import make_decision

        expense = state["expense_data"]
        applicant = state["applicant_data"]

        info = check_info_completeness(expense, applicant)

        # 信息严重缺失 → 直接驳回（跳过后续步骤）
        if not info["passed"] and len(info.get("missing_fields", [])) >= 3:
            state["info_check"] = info
            state["budget_check"] = {"passed": True, "over_budget": False}
            state["risk_analysis"] = {"risk_score": 0, "risk_level": "low", "risk_items": []}
            state["final_decision"] = {
                "conclusion": "auto_reject", "confidence": 0.95,
                "reasoning": f"信息缺失{len(info['missing_fields'])}项",
                "approval_advice": "请补充：" + "、".join(info["missing_fields"][:3]),
            }
            state["current_step"] = "completed"
            return state

        budget = check_budget_and_standards(expense, applicant)
        risk = analyze_risk(expense, applicant)
        decision = make_decision(expense, applicant, info, budget, risk)

        state["info_check"] = info
        state["budget_check"] = budget
        state["risk_analysis"] = risk
        state["final_decision"] = decision
        state["risk_score"] = risk.get("risk_score", 0)
        state["current_step"] = "completed"
        state["processing_log"] = [
            {"step": "info_check", "message": f"信息校验：{'通过' if info['passed'] else '不通过'}"},
            {"step": "budget_check", "message": f"预算校验：{'通过' if budget['passed'] else '不通过'}"},
            {"step": "risk_analysis", "message": f"风险评分：{risk.get('risk_score', 0)}"},
            {"step": "decision", "message": f"决策：{decision['conclusion']}"},
        ]
        return state

    def _check_history_violation(self, applicant: Dict) -> bool:
        """检查申请人是否有历史违规（纯代码判断）"""
        try:
            from ..tools.history_tools import get_employee_expense_history
            history = get_employee_expense_history.invoke({"employee_id": applicant.get("id", 0), "days": 90})
            reject_rate = history.get("status_distribution", {}).get("rejected", 0) / max(history.get("total_records", 1), 1)
            return reject_rate > 0.3
        except Exception:
            return False
