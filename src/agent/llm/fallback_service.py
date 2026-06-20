# -*- coding: utf-8 -*-
"""
降级知识库服务
==============
当 DeepSeek / MiMo API 不可用时，基于本地知识库提供兜底回答
严格区分问答类和审批类场景，不越权生成审批结论

文件路径：src/agent/llm/fallback_service.py
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# ── 离线模式提示文案 ──
QA_FALLBACK_SUFFIX = (
    "\n\n---\n"
    "⚠️ 当前为离线知识库模式，内容仅供参考，建议联网后获取更精准结果。"
)

APPROVAL_FALLBACK_SUFFIX = (
    "\n\n---\n"
    "⚠️ API 服务异常，已切换至规则参考模式，请人工审核。"
    "本结果仅提供制度规则参考，不做自动审批决策。"
)


class FallbackService:
    """本地知识库兜底服务"""

    def __init__(self):
        self._policy_kb = None

    @property
    def policy_kb(self):
        if self._policy_kb is None:
            try:
                from agent.knowledge.policy_kb import policy_kb
                self._policy_kb = policy_kb
            except ImportError:
                self._policy_kb = None
        return self._policy_kb

    def respond(self, query: str, scene: str = "qa") -> Dict[str, Any]:
        """
        生成降级回答

        Args:
            query: 用户查询
            scene: 场景类型
                - "qa": 问答场景 → 基于知识库检索回答
                - "approval": 审批场景 → 仅输出规则参考，不做决策
                - "analysis": 分析场景 → 返回静态统计
                - "general": 通用场景

        Returns:
            {"answer": str, "sources": list, "mode": "fallback"}
        """
        logger.info("Fallback respond: scene=%s, query_len=%d", scene, len(query))

        if scene == "approval":
            return self._approval_fallback(query)
        elif scene == "qa":
            return self._qa_fallback(query)
        elif scene == "analysis":
            return self._analysis_fallback(query)
        else:
            return self._general_fallback(query)

    def _qa_fallback(self, query: str) -> Dict[str, Any]:
        """问答场景降级：基于知识库检索"""
        sources = []
        context = ""

        if self.policy_kb:
            try:
                results = self.policy_kb.search(query, top_k=5)
                sources = [
                    {"content": r["content"][:100] + "...", "score": r["score"]}
                    for r in results
                ]
                context = "\n".join([r["content"] for r in results])
            except Exception as e:
                logger.warning("Policy KB search failed: %s", e)

        if context:
            answer = f"根据财务制度相关规定，以下是与您问题相关的内容：\n\n{context}"
        else:
            answer = self._rule_based_answer(query)

        answer += QA_FALLBACK_SUFFIX

        return {
            "answer": answer,
            "sources": sources,
            "mode": "fallback",
            "confidence": 0.3,
        }

    def _approval_fallback(self, query: str) -> Dict[str, Any]:
        """
        审批场景降级：仅输出规则参考，不做自动决策
        关键约束：不越权生成审批结论
        """
        # 提取规则参考
        rules = []
        if self.policy_kb:
            try:
                results = self.policy_kb.search(query, top_k=3)
                rules = [r["content"] for r in results]
            except Exception:
                pass

        rule_text = "\n".join([f"• {r}" for r in rules]) if rules else "暂无相关规则"

        answer = (
            "【规则参考模式】\n\n"
            "当前 AI 审批服务暂时不可用，以下为相关制度规则参考：\n\n"
            f"{rule_text}\n\n"
            "请审批人根据以上规则进行人工审核。"
        )

        answer += APPROVAL_FALLBACK_SUFFIX

        return {
            "answer": answer,
            "sources": [{"content": r[:80], "score": 1.0} for r in rules],
            "mode": "fallback",
            "decision": "manual_review",  # 降级模式强制转人工
            "confidence": 0.0,
        }

    def _analysis_fallback(self, query: str) -> Dict[str, Any]:
        """分析场景降级：返回静态数据提示"""
        return {
            "answer": (
                "数据分析服务暂时不可用，无法执行实时数据查询。\n"
                "请稍后重试或联系系统管理员。"
                + QA_FALLBACK_SUFFIX
            ),
            "sources": [],
            "mode": "fallback",
        }

    def _general_fallback(self, query: str) -> Dict[str, Any]:
        """通用降级"""
        return {
            "answer": (
                "AI 服务暂时不可用，已切换至离线知识库模式。\n"
                "如需帮助，请参考财务制度手册或联系财务部门。"
                + QA_FALLBACK_SUFFIX
            ),
            "sources": [],
            "mode": "fallback",
        }

    def _rule_based_answer(self, query: str) -> str:
        """基于关键词的规则匹配回答（知识库不可用时的最后兜底）"""
        q = query.lower()

        if any(kw in q for kw in ["差旅", "出差", "住宿"]):
            return (
                "差旅费报销标准（按职级）：\n"
                "专员 ¥400/天、高级专员 ¥500/天、主管 ¥600/天、\n"
                "经理 ¥800/天、高级经理 ¥1000/天、总监 ¥1500/天。\n"
                "超出标准需部门经理特批。出差结束后5个工作日内提交报销。"
            )
        elif any(kw in q for kw in ["餐饮", "招待", "聚餐"]):
            return (
                "餐饮费标准（按职级）：\n"
                "专员 ¥150/餐、高级专员 ¥200/餐、主管 ¥250/餐、\n"
                "经理 ¥300/餐。商务宴请需事前审批，单次不超过 ¥3000。"
            )
        elif any(kw in q for kw in ["审批", "流程"]):
            return (
                "报销审批流程（按金额分级）：\n"
                "• ¥1000 以下：员工→部门经理→财务（2级）\n"
                "• ¥1000-5000：员工→部门经理→财务→财务总监（3级）\n"
                "• ¥5000 以上：员工→部门经理→财务→财务总监→总经理（4级）\n"
                "驳回后可修改重新提交。"
            )
        elif any(kw in q for kw in ["发票", "票据"]):
            return (
                "发票要求：\n"
                "• 抬头必须为公司全称\n"
                "• 增值税专用发票30日内认证\n"
                "• 电子发票需打印纸质版\n"
                "• 虚假发票将追究责任"
            )
        elif any(kw in q for kw in ["预算", "额度"]):
            return (
                "预算管理规定：\n"
                "• 每年12月编制下年度预算\n"
                "• 使用率超80%预警，超100%冻结\n"
                "• 超预算需提前申请追加"
            )
        else:
            return "未找到直接相关的制度条文，建议咨询财务部门获取准确信息。"


# 全局单例
fallback_service = FallbackService()
