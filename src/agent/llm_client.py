# -*- coding: utf-8 -*-
"""
LLM 客户端兼容层
=================
转发到 agent.llm.llm_client，保持向后兼容

文件路径：src/agent/llm_client.py
"""

# 向后兼容：所有旧的 from agent.llm_client import get_llm 仍然有效
from agent.llm.llm_client import get_llm, chat, chat_stream, is_fallback_active, get_fallback_info

__all__ = ["get_llm", "chat", "chat_stream", "is_fallback_active", "get_fallback_info"]
