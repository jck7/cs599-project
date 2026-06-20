# -*- coding: utf-8 -*-
"""
MiMo API 连通性快速验证
========================
运行：cd d:/cs599-project && python -m agent.verify_mimo
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def main():
    print("=" * 50)
    print("  MiMo API 连通性验证")
    print("=" * 50)

    # 1. 检查配置
    from agent.config import AgentConfig
    print()
    print("[1] 环境变量检查")
    print(f"    LLM_PROVIDER:    {AgentConfig.LLM_PROVIDER}")
    print(f"    USE_REAL_LLM:    {AgentConfig.USE_REAL_LLM}")
    print(f"    MIMO_API_KEY:    {'已配置 (' + AgentConfig.MIMO_API_KEY[:8] + '...)' if AgentConfig.MIMO_API_KEY else '❌ 未配置'}")
    print(f"    MIMO_BASE_URL:   {AgentConfig.MIMO_BASE_URL}")
    print(f"    MIMO_MODEL_NAME: {AgentConfig.MIMO_MODEL_NAME}")

    if not AgentConfig.USE_REAL_LLM:
        print()
        print("⚠️  USE_REAL_LLM=false，当前使用规则引擎，未调用任何 LLM")
        print("    如需启用 MiMo，请在 .env 中设置：")
        print("    USE_REAL_LLM=true")
        print("    MIMO_API_KEY=your_key")
        return

    if not AgentConfig.MIMO_API_KEY:
        print()
        print("❌ MIMO_API_KEY 未配置，请在 .env 中设置")
        return

    # 2. 检查 LLM 客户端
    print()
    print("[2] LLM 客户端初始化")
    from agent.llm_client import get_llm
    llm = get_llm()
    if not llm:
        print("    ❌ LLM 初始化失败")
        return

    print(f"    客户端类型: {type(llm).__name__}")
    print(f"    模型名称:   {llm.model_name if hasattr(llm, 'model_name') else 'N/A'}")
    print(f"    base_url:   {llm.openai_api_base if hasattr(llm, 'openai_api_base') else 'N/A'}")

    # 3. 实际调用测试
    print()
    print("[3] 实际 API 调用测试")
    from langchain_core.messages import HumanMessage

    try:
        resp = llm.invoke([HumanMessage(content="请回复'MiMo连接成功'四个字")])
        content = resp.content if hasattr(resp, "content") else str(resp)
        print(f"    回复内容: {content}")

        # 检查是否返回了有效内容
        if content and len(content) > 0:
            print("    ✅ MiMo API 调用成功")
        else:
            print("    ⚠️  返回内容为空")

        # 检查额外信息（如 reasoning_content）
        if hasattr(resp, "additional_kwargs") and resp.additional_kwargs:
            reasoning = resp.additional_kwargs.get("reasoning_content", "")
            if reasoning:
                print(f"    思考过程: {reasoning[:100]}...")

    except Exception as e:
        print(f"    ❌ 调用失败: {e}")
        err_str = str(e).lower()
        if "401" in err_str or "auth" in err_str or "key" in err_str:
            print("    → 可能是 API Key 无效，请检查 MIMO_API_KEY")
        elif "timeout" in err_str:
            print("    → 网络超时，请检查网络连接或 MIMO_BASE_URL")
        elif "404" in err_str or "model" in err_str:
            print("    → 模型不存在，请检查 MIMO_MODEL_NAME")
        return

    # 4. 完整审批流测试
    print()
    print("[4] 完整审批流测试（MiMo 驱动）")
    from agent.service import agent_service
    result = agent_service.analyze_expense(1)

    if "error" in result and result.get("error") and not result.get("final_decision"):
        print(f"    ❌ 分析失败: {result['error']}")
    else:
        d = result.get("final_decision", {})
        print(f"    决策结论: {d.get('conclusion', 'N/A')}")
        print(f"    推理过程: {d.get('reasoning', 'N/A')[:80]}...")
        print("    ✅ 审批流运行正常")

    print()
    print("=" * 50)
    print("  验证完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
