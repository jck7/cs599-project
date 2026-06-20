# -*- coding: utf-8 -*-
"""
审批全局状态定义
===============
LangGraph 工作流的共享状态结构
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    """单项校验结果"""
    passed: bool = True
    message: str = ""
    details: List[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    """风险项"""
    type: str = ""
    level: Literal["low", "medium", "high", "critical"] = "low"
    description: str = ""
    score: int = 0


class AgentDecision(BaseModel):
    """Agent 审批决策"""
    conclusion: Literal["auto_approve", "auto_reject", "manual_review", "error"] = "manual_review"
    confidence: float = 0.0
    reasoning: str = ""
    suggested_action: str = ""
    recommended_node: str = ""
    approval_advice: str = ""


class ApprovalState(TypedDict):
    """LangGraph 审批工作流全局状态"""

    # ── 输入 ──
    expense_id: int
    expense_data: Dict[str, Any]          # 报销单原始数据
    applicant_data: Dict[str, Any]        # 申请人信息
    department_data: Dict[str, Any]       # 部门信息

    # ── 各节点校验结果 ──
    info_check: Optional[Dict[str, Any]]         # 信息完整性校验
    budget_check: Optional[Dict[str, Any]]       # 预算校验
    risk_analysis: Optional[Dict[str, Any]]      # 风险分析
    final_decision: Optional[Dict[str, Any]]     # 最终决策

    # ── 流程控制 ──
    current_step: str                     # 当前步骤名称
    error_message: Optional[str]          # 错误信息
    processing_log: List[Dict[str, Any]]  # 处理日志

    # ── 输出 ──
    risk_score: int                       # 0-100 风险评分
    auto_decision: str                    # 自动决策结论
    human_advice: str                     # 给人工审批的建议
    final_action: str                     # 最终动作
