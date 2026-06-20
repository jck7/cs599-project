# -*- coding: utf-8 -*-
"""
风险识别 Agent（精简版）
提示词极致瘦身，只保留核心任务+输出格式
"""

from typing import Dict, Any
from ..config import AgentConfig


def analyze_risk(expense: Dict, applicant: Dict) -> Dict[str, Any]:
    """风险分析：规则+LLM混合"""
    amount = expense.get("amount", 0)
    risk_items = []
    score = 0

    # 硬规则前置（不走LLM）
    if amount >= 5000:
        score += 15
        risk_items.append({"type": "large_amount", "level": "medium", "score": 15})
    elif amount >= 2000:
        score += 8
        risk_items.append({"type": "moderate_amount", "level": "low", "score": 8})

    # 历史行为检测
    try:
        from ..tools.history_tools import detect_frequency_anomaly, detect_amount_spike
        freq = detect_frequency_anomaly.invoke({"employee_id": applicant.get("id", 0), "days": 30, "threshold": 5})
        if freq.get("is_anomaly"):
            score += 20
            risk_items.append({"type": "frequency", "level": "medium", "score": 20})

        spike = detect_amount_spike.invoke({"employee_id": applicant.get("id", 0), "days": 90})
        if spike.get("has_spike"):
            score += 25
            risk_items.append({"type": "spike", "level": "high", "score": 25})
    except Exception:
        pass

    score = min(score, 100)
    level = "high" if score >= 60 else "medium" if score >= 30 else "low"

    # 仅高风险时调用LLM做深度分析
    if score >= 30 and AgentConfig.USE_REAL_LLM:
        llm_result = _llm_risk_analysis(expense, applicant, score)
        if llm_result:
            return llm_result

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_items": risk_items,
        "summary": f"风险评分{score}/100（{level}）",
    }


def _llm_risk_analysis(expense: Dict, applicant: Dict, rule_score: int) -> Dict[str, Any]:
    """LLM深度风险分析（仅高风险触发）"""
    from agent.llm.llm_client import chat
    from langchain_core.messages import HumanMessage
    import json

    # 极简提示词：只给核心数据
    prompt = (
        f"分析报销风险，输出JSON：\n"
        f"金额：¥{expense.get('amount', 0)}\n"
        f"类型：{expense.get('detail', [{}])[0].get('type', 'OTHER')}\n"
        f"申请人：{applicant.get('level', '')}\n"
        f"规则评分：{rule_score}\n"
        f'{{"risk_score":0-100,"risk_items":[{{"type":"","level":"","description":""}}]}}'
    )

    result = chat([HumanMessage(content=prompt)], scene="risk")
    if result["success"] and result["source"] != "fallback":
        try:
            d = json.loads(result["content"])
            d.setdefault("risk_level", "high" if d.get("risk_score", 0) >= 60 else "medium")
            d.setdefault("summary", f"风险评分{d.get('risk_score', 0)}/100")
            return d
        except Exception:
            pass
    return None
