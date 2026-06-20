# -*- coding: utf-8 -*-
"""
FastAPI 智能审批服务
====================
独立运行，与原 Flask 系统解耦
运行方式: python -m agent.api 或 uvicorn agent.api:app
"""

import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# 确保路径
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.config import AgentConfig
from agent.service import agent_service

# ── FastAPI 应用 ──
app = FastAPI(
    title="智能审批 Agent 服务",
    description="基于 LangGraph + DeepSeek 的多步骤审批工作流",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求/响应模型 ──
class AnalyzeRequest(BaseModel):
    expense_id: int


class AnalyzeResponse(BaseModel):
    expense_id: int
    info_check: Optional[dict] = None
    budget_check: Optional[dict] = None
    risk_analysis: Optional[dict] = None
    final_decision: Optional[dict] = None
    processing_log: list = []
    user_profile: Optional[dict] = None
    analyzed_at: str = ""
    error: Optional[str] = None


class BatchAnalyzeRequest(BaseModel):
    expense_ids: List[int]


class DashboardStats(BaseModel):
    total_processed: int = 0
    auto_approved: int = 0
    auto_rejected: int = 0
    manual_review: int = 0
    auto_rate: float = 0.0
    avg_process_time_sec: float = 0.0
    risk_intercepted: int = 0
    human_intervention_rate: float = 0.0


# ── API 路由 ──
@app.get("/health")
def health():
    """健康检查"""
    # 检测当前活跃的 LLM 提供方
    provider = AgentConfig.LLM_PROVIDER
    active = "none"
    if AgentConfig.USE_REAL_LLM:
        if provider == "mimo" or (provider == "auto" and AgentConfig.MIMO_API_KEY):
            active = "mimo"
        elif provider == "deepseek" or (provider == "auto" and AgentConfig.DEEPSEEK_API_KEY):
            active = "deepseek"
        else:
            active = "unconfigured"
    return {
        "status": "ok",
        "service": "ai-approval-agent",
        "timestamp": datetime.now().isoformat(),
        "llm_enabled": AgentConfig.USE_REAL_LLM,
        "llm_provider": provider,
        "llm_active": active,
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_expense(req: AnalyzeRequest):
    """对指定报销单执行 AI 审批分析"""
    try:
        result = agent_service.analyze_expense(req.expense_id)
        if "error" in result and result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        return AnalyzeResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/analyze/batch")
def batch_analyze(req: BatchAnalyzeRequest):
    """批量分析多个报销单"""
    results = []
    for eid in req.expense_ids[:20]:  # 限制最多 20 条
        try:
            result = agent_service.analyze_expense(eid)
            results.append(result)
        except Exception as e:
            results.append({"expense_id": eid, "error": str(e)})
    return {"results": results, "count": len(results)}


@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard_stats():
    """获取 AI 审批看板统计数据"""
    try:
        stats = agent_service.get_dashboard_stats()
        return DashboardStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
def get_config():
    """获取当前 Agent 配置（脱敏）"""
    return {
        "llm_model": AgentConfig.LLM_MODEL,
        "use_real_llm": AgentConfig.USE_REAL_LLM,
        "risk_low": AgentConfig.RISK_LOW_THRESHOLD,
        "risk_medium": AgentConfig.RISK_MEDIUM_THRESHOLD,
        "risk_high": AgentConfig.RISK_HIGH_THRESHOLD,
        "auto_approve_amount": AgentConfig.AUTO_APPROVE_AMOUNT,
        "manual_review_amount": AgentConfig.MANUAL_REVIEW_AMOUNT,
        "langsmith_tracing": AgentConfig.LANGSMITH_TRACING,
    }


# ── 新增：填报助手 API ──
class FillAssistRequest(BaseModel):
    employee_id: int
    text: str = ""
    current_items: list = []


@app.post("/api/fill/assist")
def fill_assist(req: FillAssistRequest):
    """填报智能辅助"""
    try:
        result = agent_service.get_fill_assistance(
            employee_id=req.employee_id,
            text=req.text,
            current_items=req.current_items,
        )
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 新增：合规审计 API ──
class AuditRequest(BaseModel):
    days: int = 30
    risk_level: str = "all"


@app.post("/api/audit/scan")
def audit_scan(req: AuditRequest):
    """执行合规审计扫描"""
    try:
        result = agent_service.run_compliance_audit(days=req.days, risk_level=req.risk_level)
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 新增：知识问答 API ──
class QARequest(BaseModel):
    question: str
    user_id: int = 0
    user_level: str = ""
    user_dept: str = ""
    history: list = []


@app.post("/api/qa/ask")
def qa_ask(req: QARequest):
    """财务制度智能问答"""
    try:
        result = agent_service.ask_question(
            question=req.question,
            user_id=req.user_id,
            user_level=req.user_level,
            user_dept=req.user_dept,
            history=req.history,
        )
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 新增：数据分析 API ──
class AnalysisRequest(BaseModel):
    query: str


@app.post("/api/analysis/query")
def analysis_query(req: AnalysisRequest):
    """自然语言数据分析"""
    try:
        result = agent_service.analyze_data(req.query)
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 新增：Supervisor 状态 ──
@app.get("/api/supervisor/status")
def supervisor_status():
    """获取多智能体协调状态"""
    from agent.orchestrator.supervisor_agent import supervisor
    return supervisor.get_agent_status()


@app.get("/api/supervisor/history")
def supervisor_history(limit: int = 20):
    """获取任务历史"""
    from agent.orchestrator.supervisor_agent import supervisor
    return {"tasks": supervisor.get_task_history(limit)}


# ── 启动 ──
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  智能审批 Agent 服务")
    print(f"  http://{AgentConfig.SERVER_HOST}:{AgentConfig.SERVER_PORT}")
    print("=" * 50)
    uvicorn.run(app, host=AgentConfig.SERVER_HOST, port=AgentConfig.SERVER_PORT)
