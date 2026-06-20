# -*- coding: utf-8 -*-
"""
统一 LLM 客户端（极致性能版）
==============================
优化：单例缓存、场景参数分级、禁用无效深度思考

文件路径：src/agent/llm/llm_client.py
"""

import time
import logging
from typing import Optional, Any, Dict, Generator

logger = logging.getLogger(__name__)

_fallback_active = False
_fallback_reason = ""
_fallback_since = ""

# 单例缓存：key = "provider_scene"，value = LLM 实例
_llm_cache: Dict[str, Any] = {}

# 场景参数分级
_PARAMS = {
    # 普通问答/信息校验/预算校验：快速响应
    "qa":       {"max_tokens": 800,  "temperature": 0.3},
    "info":     {"max_tokens": 512,  "temperature": 0.1},
    "budget":   {"max_tokens": 512,  "temperature": 0.1},
    # 风险识别/审批决策：深度推理
    "risk":     {"max_tokens": 1024, "temperature": 0.3},
    "approval": {"max_tokens": 1024, "temperature": 0.3},
    # 工具调用：严格服从
    "tool":     {"max_tokens": 1024, "temperature": 0.1},
    # 测试
    "test":     {"max_tokens": 64,   "temperature": 0.1},
}


def is_fallback_active() -> bool:
    return _fallback_active


def get_fallback_info() -> Dict[str, Any]:
    return {"fallback_active": _fallback_active, "fallback_reason": _fallback_reason, "fallback_since": _fallback_since}


def get_llm(scene: str = "general") -> Any:
    """获取 LLM 单例（按场景缓存）"""
    from agent.config import AgentConfig
    if not AgentConfig.USE_REAL_LLM:
        return None

    provider = AgentConfig.LLM_PROVIDER
    cache_key = f"{provider}_{scene}"
    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    params = _PARAMS.get(scene, _PARAMS["qa"])
    llm = None

    if provider in ("mimo", "auto") and AgentConfig.MIMO_API_KEY:
        llm = _init_mimo(params)
    if not llm and provider in ("deepseek", "auto") and AgentConfig.DEEPSEEK_API_KEY:
        llm = _init_deepseek(params)

    if llm:
        _llm_cache[cache_key] = llm
        logger.info("[LLM] Cached: scene=%s", scene)
    return llm


def _init_deepseek(params: dict):
    from agent.config import AgentConfig
    try:
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(
            model=AgentConfig.DEEPSEEK_MODEL,
            api_key=AgentConfig.DEEPSEEK_API_KEY,
            base_url=AgentConfig.DEEPSEEK_BASE_URL,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            timeout=AgentConfig.LLM_TIMEOUT,
        )
    except Exception as e:
        logger.error("[LLM] DeepSeek init failed: %s", e)
        return None


def _init_mimo(params: dict):
    from agent.config import AgentConfig
    if not AgentConfig.MIMO_API_KEY:
        return None
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=AgentConfig.MIMO_MODEL_NAME,
            api_key=AgentConfig.MIMO_API_KEY,
            base_url=AgentConfig.MIMO_BASE_URL,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            timeout=AgentConfig.LLM_TIMEOUT,
        )
    except Exception as e:
        logger.error("[LLM] MiMo init failed: %s", e)
        return None


def _enter_fallback(reason: str):
    global _fallback_active, _fallback_reason, _fallback_since
    if not _fallback_active:
        _fallback_active = True
        _fallback_reason = reason
        _fallback_since = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.warning("[FALLBACK] %s", reason[:100])


def _exit_fallback():
    global _fallback_active, _fallback_reason, _fallback_since
    if _fallback_active:
        _fallback_active = False
        _fallback_reason = ""
        _fallback_since = ""


def chat(messages: list, tools: list = None, scene: str = "general") -> Dict[str, Any]:
    """统一对话入口（单例+场景参数+重试+降级）"""
    from agent.config import AgentConfig

    if not AgentConfig.USE_REAL_LLM:
        return _fallback_respond(messages, scene)

    _exit_fallback()
    llm = get_llm(scene=scene)
    if not llm:
        return _fallback_respond(messages, scene)

    max_retries = AgentConfig.LLM_MAX_RETRIES
    retry_delay = AgentConfig.LLM_RETRY_DELAY
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            llm_to_use = llm.bind_tools(tools) if tools else llm
            resp = llm_to_use.invoke(messages)
            _exit_fallback()

            content = resp.content if hasattr(resp, "content") else str(resp)
            result = {
                "content": content,
                "tool_calls": resp.tool_calls if hasattr(resp, "tool_calls") else [],
                "source": _detect_provider(llm),
                "success": True,
                "error": "",
            }
            if hasattr(resp, "additional_kwargs"):
                rc = resp.additional_kwargs.get("reasoning_content", "")
                if rc:
                    result["reasoning"] = rc
            return result

        except Exception as e:
            last_error = str(e)
            if _is_retryable(e) and attempt < max_retries:
                time.sleep(retry_delay)
                continue
            elif not _is_retryable(e):
                break

    _enter_fallback(f"API failed: {last_error[:100]}")
    if AgentConfig.LLM_FALLBACK_ENABLED:
        return _fallback_respond(messages, scene)
    return {"content": "", "tool_calls": [], "source": "error", "success": False, "error": last_error or "LLM unavailable"}


def chat_stream(messages: list, tools: list = None, scene: str = "qa") -> Generator:
    """SSE 流式输出"""
    from agent.config import AgentConfig

    if not AgentConfig.USE_REAL_LLM:
        r = _fallback_respond(messages, scene)
        yield {"chunk": r["content"], "done": True, "source": "fallback"}
        return

    _exit_fallback()
    llm = get_llm(scene=scene)
    if not llm:
        r = _fallback_respond(messages, scene)
        yield {"chunk": r["content"], "done": True, "source": "fallback"}
        return

    try:
        llm_to_use = llm.bind_tools(tools) if tools else llm
        for chunk in llm_to_use.stream(messages):
            c = chunk.content if hasattr(chunk, "content") else ""
            if c:
                yield {"chunk": c, "done": False, "source": _detect_provider(llm)}
        yield {"chunk": "", "done": True, "source": _detect_provider(llm)}
        _exit_fallback()
    except Exception as e:
        logger.error("[LLM] Stream failed: %s", e)
        _enter_fallback(str(e)[:80])
        if AgentConfig.LLM_FALLBACK_ENABLED:
            r = _fallback_respond(messages, scene)
            yield {"chunk": r["content"], "done": True, "source": "fallback"}
        else:
            yield {"chunk": "", "done": True, "source": "error", "error": str(e)}


def _is_retryable(e: Exception) -> bool:
    err = str(e).lower()
    for kw in ["401", "403", "authentication", "invalid api key", "model not found", "400"]:
        if kw in err:
            return False
    for kw in ["timeout", "connection", "502", "503", "504", "429"]:
        if kw in err:
            return True
    return True


def _fallback_respond(messages: list, scene: str) -> Dict[str, Any]:
    from agent.llm.fallback_service import fallback_service
    query = ""
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            query = msg.content
            break
    result = fallback_service.respond(query, scene=scene)
    return {"content": result["answer"], "tool_calls": [], "source": "fallback", "success": True, "error": "", "fallback_info": get_fallback_info()}


def _detect_provider(llm) -> str:
    n = type(llm).__name__.lower()
    if "deepseek" in n: return "deepseek"
    if "openai" in n: return "mimo"
    return "unknown"
