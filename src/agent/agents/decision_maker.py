# -*- coding: utf-8 -*-
"""
审批决策 Agent（极致性能版）
============================
极速通道：fast_decision() - 1次LLM调用
标准/严格通道：make_decision() - 1次LLM调用
规则引擎：_rule_decision() - 0次LLM调用
"""

from typing import Dict, Any
from ..config import AgentConfig


def fast_decision(expense: Dict, applicant: Dict, info: Dict, budget: Dict) -> Dict[str, Any]:
    """极速通道决策（<1000元低风险）"""
    amount = expense.get("amount", 0)

    # 硬规则：信息缺失→驳回
    if not info["passed"] and len(info.get("missing_fields", [])) >= 2:
        return _build("auto_reject", 0.95, f"信息缺失{len(info['missing_fields'])}项",
                       "请补充后重新提交")

    # 硬规则：预算不足→驳回
    if budget.get("over_budget"):
        return _build("auto_reject", 0.9, "部门预算不足", "请联系财务追加预算")

    # 低风险小金额→自动通过
    if not budget.get("over_standard_count"):
        return _build("auto_approve", 0.92, f"低风险小额¥{amount:.0f}，各项校验通过", "自动审批通过")

    # 有超标项→转人工
    return _build("manual_review", 0.8, f"有{budget.get('over_standard_count', 0)}项超标", "请审批人判断")


def make_decision(expense: Dict, applicant: Dict, info: Dict, budget: Dict, risk: Dict) -> Dict[str, Any]:
    """标准/严格通道决策"""
    amount = expense.get("amount", 0)
    risk_score = risk.get("risk_score", 0)

    # 硬规则前置
    if not info["passed"] and len(info.get("missing_fields", [])) >= 3:
        return _build("auto_reject", 0.95, "信息严重缺失",
                       "请补充：" + "、".join(info["missing_fields"][:3]))

    if risk_score >= 80:
        return _build("auto_reject", 0.9, f"高风险{risk_score}分",
                       "存在多项风险，请重新核实")

    if risk_score < 30 and amount < 1000 and info["passed"] and not budget.get("over_budget"):
        return _build("auto_approve", 0.9, "低风险+小额+各项通过", "自动审批")

    # LLM辅助决策
    if AgentConfig.USE_REAL_LLM:
        return _llm_decision(expense, applicant, info, budget, risk)

    return _build("manual_review", 0.7, f"风险{risk_score}分，金额¥{amount:.0f}",
                   "请审批人综合判断")


def _llm_decision(expense: Dict, applicant: Dict, info: Dict, budget: Dict, risk: Dict) -> Dict[str, Any]:
    """LLM辅助决策（精简prompt）"""
    from agent.llm.llm_client import chat
    from langchain_core.messages import HumanMessage
    import json

    # 极简prompt：只传核心字段
    prompt = (
        f"审批决策，输出JSON：\n"
        f"金额¥{expense.get('amount', 0)}，申请人{applicant.get('level','')}，"
        f"信息{'通过' if info.get('passed') else '不通过'}，"
        f"预算{'充足' if not budget.get('over_budget') else '不足'}，"
        f"风险{risk.get('risk_score',0)}分\n"
        f'{{"conclusion":"auto_approve/auto_reject/manual_review","confidence":0.0-1.0,"reasoning":"原因","approval_advice":"建议"}}'
    )

    result = chat([HumanMessage(content=prompt)], scene="approval")
    if result["success"] and result["source"] != "fallback":
        try:
            d = json.loads(result["content"])
            return _build(d.get("conclusion", "manual_review"), d.get("confidence", 0.7),
                          d.get("reasoning", ""), d.get("approval_advice", ""))
        except Exception:
            pass

    return _build("manual_review", 0.6, "需人工判断", "请审批人综合评估")


def _build(conclusion: str, confidence: float, reasoning: str, advice: str) -> Dict[str, Any]:
    return {
        "conclusion": conclusion,
        "confidence": confidence,
        "reasoning": reasoning,
        "suggested_action": {"auto_approve": "自动通过", "auto_reject": "自动驳回"}.get(conclusion, "转人工"),
        "approval_advice": advice,
    }
