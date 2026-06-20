# -*- coding: utf-8 -*-
"""
财务制度智能问答 Agent（性能优化版）
====================================
优化：意图分流跳过RAG、精简prompt、场景化参数

文件路径：src/agent/agents/qa_agent.py
"""

import logging
from typing import Dict, Any
from ..knowledge.policy_kb import policy_kb
from ..config import AgentConfig

logger = logging.getLogger(__name__)

# 财务关键词（命中才走RAG）
_FINANCE_KW = frozenset([
    "报销", "差旅", "出差", "餐饮", "交通", "住宿", "发票", "审批",
    "预算", "额度", "标准", "流程", "制度", "规定", "招待", "培训",
    "办公", "打款", "归档", "驳回", "撤回", "超标", "合规", "费用",
])


def answer_question(question: str, user_id: int = 0, user_level: str = "",
                    user_dept: str = "", history: list = None) -> Dict[str, Any]:
    from agent.llm.llm_client import chat, is_fallback_active
    from langchain_core.messages import HumanMessage

    # 意图判断（关键词匹配，<1ms）
    is_finance = any(kw in question for kw in _FINANCE_KW)

    # 仅财务类问题走RAG检索
    rag_context = ""
    sources = []
    if is_finance:
        try:
            results = policy_kb.search(question, top_k=3)
            if results and results[0].get("score", 0) > 0.15:
                rag_context = "\n".join([r["content"] for r in results])
                sources = [{"content": r["content"][:100] + "...", "score": r["score"]} for r in results]
        except Exception:
            pass

    # 构建精简prompt
    prompt = _build_prompt(question, rag_context, user_level, is_finance)

    # 调用LLM（单例+场景参数）
    result = chat(messages=[HumanMessage(content=prompt)], scene="qa")

    related = _generate_related_questions(question)

    if result["success"] and result["source"] != "fallback":
        llm_used = "rag_enhanced" if (is_finance and rag_context) else result["source"]
        return {
            "answer": result["content"],
            "sources": sources,
            "confidence": 0.85 if is_finance else 0.75,
            "related_questions": related,
            "context_used": rag_context[:300] if rag_context else "",
            "llm_used": llm_used,
            "model_name": _get_model_name(result["source"]),
        }

    # 降级
    from agent.llm.fallback_service import fallback_service
    fb = fallback_service.respond(question, scene="qa")
    return {
        "answer": fb["answer"],
        "sources": fb.get("sources", []),
        "confidence": 0.3,
        "related_questions": related,
        "context_used": "",
        "llm_used": "fallback",
        "model_name": "",
    }


def _build_prompt(question: str, rag_context: str, user_level: str, is_finance: bool) -> str:
    """精简prompt，减少输入token"""
    if is_finance and rag_context:
        return (
            f"你是企业财务报销制度专家。请结合以下参考资料回答。\n"
            f"参考资料：\n{rag_context}\n"
            f"用户职级：{user_level or '未知'}\n"
            f"问题：{question}\n"
            f"请专业准确地回答："
        )
    elif is_finance:
        return (
            f"你是企业财务报销制度专家。知识库中无直接相关内容，请用专业知识回答。\n"
            f"问题：{question}\n请回答："
        )
    else:
        return f"请直接回答：{question}"


def _get_model_name(source: str) -> str:
    if source == "deepseek":
        return AgentConfig.DEEPSEEK_MODEL
    elif source == "mimo":
        return AgentConfig.MIMO_MODEL_NAME
    return ""


def _generate_related_questions(question: str) -> list:
    q = question
    if any(kw in q for kw in ["差旅", "出差", "住宿"]):
        return ["差旅费报销需要哪些材料？", "超出差旅标准怎么办？", "出差审批流程是什么？"]
    elif any(kw in q for kw in ["餐饮", "招待"]):
        return ["商务招待费标准？", "聚餐报销需要什么凭证？", "招待费审批流程？"]
    elif any(kw in q for kw in ["审批", "流程"]):
        return ["报销审批需要多长时间？", "被驳回后怎么处理？", "大额报销审批流程？"]
    elif any(kw in q for kw in ["发票", "票据"]):
        return ["电子发票可以报销吗？", "发票丢失怎么办？", "发票抬头要求？"]
    elif any(kw in q for kw in ["预算", "额度"]):
        return ["如何查看部门预算剩余？", "超预算了还能报销吗？", "预算追加流程？"]
    return ["差旅费报销标准？", "报销审批流程？", "发票要求？"]
