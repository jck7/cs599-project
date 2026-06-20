# -*- coding: utf-8 -*-
"""
Agent 配置管理（DeepSeek 主模型 + 自动降级）
============================================
所有配置从环境变量读取，严禁硬编码 API Key

文件路径：src/agent/config.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（项目根目录）
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


class AgentConfig:
    """Agent 全局配置"""

    # ── DeepSeek API 配置（主模型） ──
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # ── MiMo API 配置（备用模型，保留兼容） ──
    MIMO_API_KEY: str = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL: str = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    MIMO_MODEL_NAME: str = os.getenv("MIMO_MODEL_NAME", "mimo-v2.5-pro")

    # ── LLM 提供方选择（deepseek / mimo / auto） ──
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")

    # ── 通用 LLM 参数 ──
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))

    # ── 重试与降级配置 ──
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    LLM_RETRY_DELAY: float = float(os.getenv("LLM_RETRY_DELAY", "1.0"))
    LLM_FALLBACK_ENABLED: bool = os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true"

    # ── 是否启用真实 LLM ──
    USE_REAL_LLM: bool = os.getenv("USE_REAL_LLM", "false").lower() == "true"

    # ── LangSmith 可观测性 ──
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "cs599-oa-agent")

    # ── 服务配置 ──
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # ── Agent 业务规则配置 ──
    RISK_LOW_THRESHOLD: int = int(os.getenv("RISK_LOW_THRESHOLD", "30"))
    RISK_MEDIUM_THRESHOLD: int = int(os.getenv("RISK_MEDIUM_THRESHOLD", "60"))
    RISK_HIGH_THRESHOLD: int = int(os.getenv("RISK_HIGH_THRESHOLD", "80"))
    AUTO_APPROVE_AMOUNT: float = float(os.getenv("AUTO_APPROVE_AMOUNT", "1000"))
    MANUAL_REVIEW_AMOUNT: float = float(os.getenv("MANUAL_REVIEW_AMOUNT", "5000"))

    @classmethod
    def get_llm(cls):
        """获取 LLM 实例（委托给 llm. llm_client 统一处理）"""
        if not cls.USE_REAL_LLM:
            return None
        from agent.llm.llm_client import get_llm
        return get_llm()

    @classmethod
    def setup_langsmith(cls):
        """配置 LangSmith 追踪"""
        if cls.LANGSMITH_TRACING and cls.LANGSMITH_API_KEY:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = cls.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = cls.LANGSMITH_PROJECT
