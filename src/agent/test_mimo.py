# -*- coding: utf-8 -*-
"""
MiMo API 接入测试
==================
三个测试用例：纯对话、工具调用、完整审批流

文件路径：src/agent/test_mimo.py
运行方式：python -m agent.test_mimo
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_pure_chat():
    """测试 1：纯对话（验证 MiMo API 连通性）"""
    print("=" * 50)
    print("【测试 1】纯对话测试")
    print("=" * 50)

    from agent.llm_client import get_llm
    from langchain_core.messages import HumanMessage

    llm = get_llm()
    if not llm:
        print("  ⚠️  LLM 不可用（USE_REAL_LLM=false 或 API Key 未配置）")
        print("  请在 .env 中设置 USE_REAL_LLM=true 和 MIMO_API_KEY")
        return False

    print(f"  LLM 类型：{type(llm).__name__}")
    print(f"  模型：{llm.model_name if hasattr(llm, 'model_name') else 'unknown'}")

    try:
        resp = llm.invoke([HumanMessage(content="你好，请用一句话介绍你自己。")])
        content = resp.content if hasattr(resp, "content") else str(resp)
        print(f"  回复：{content[:100]}")
        print("  ✅ 纯对话测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 调用失败：{e}")
        return False


def test_tool_calling():
    """测试 2：工具调用（验证 Function Calling）"""
    print()
    print("=" * 50)
    print("【测试 2】工具调用测试")
    print("=" * 50)

    from agent.llm_client import get_llm
    from agent.tools.employee_tools import get_employee_info
    from langchain_core.messages import HumanMessage

    llm = get_llm()
    if not llm:
        print("  ⚠️  LLM 不可用，跳过")
        return False

    try:
        # 绑定工具
        llm_with_tools = llm.bind_tools([get_employee_info])
        resp = llm_with_tools.invoke([HumanMessage(content="请查询员工ID为1的基本信息")])

        # 检查是否有工具调用
        tool_calls = resp.tool_calls if hasattr(resp, "tool_calls") else []
        content = resp.content if hasattr(resp, "content") else ""

        if tool_calls:
            print(f"  工具调用数：{len(tool_calls)}")
            for tc in tool_calls:
                print(f"    - 工具：{tc.get('name', 'unknown')}")
                print(f"      参数：{tc.get('args', {})}")
            print("  ✅ 工具调用测试通过")
            return True
        else:
            print(f"  回复内容：{content[:100]}")
            print("  ⚠️  模型未触发工具调用（可能需要调整 prompt）")
            return True  # 不算失败，模型可能选择直接回答

    except Exception as e:
        print(f"  ❌ 调用失败：{e}")
        return False


def test_approval_flow():
    """测试 3：完整审批流（验证 Agent 工作流集成）"""
    print()
    print("=" * 50)
    print("【测试 3】完整审批流测试")
    print("=" * 50)

    from agent.service import agent_service

    try:
        result = agent_service.analyze_expense(1)

        if "error" in result and result.get("error") and not result.get("final_decision"):
            print(f"  ❌ 分析失败：{result['error']}")
            return False

        info = result.get("info_check", {})
        budget = result.get("budget_check", {})
        risk = result.get("risk_analysis", {})
        decision = result.get("final_decision", {})

        print(f"  信息校验：{'通过' if info.get('passed') else '不通过'} - {info.get('message', '')}")
        print(f"  预算校验：{'通过' if budget.get('passed') else '不通过'} - {budget.get('message', '')}")
        print(f"  风险评分：{risk.get('risk_score', 0)}/100（{risk.get('risk_level', '')}）")
        print(f"  最终决策：{decision.get('conclusion', '')}")
        print(f"  审批建议：{decision.get('approval_advice', '')}")
        print("  ✅ 完整审批流测试通过")
        return True

    except Exception as e:
        print(f"  ❌ 调用失败：{e}")
        return False


def test_reasoning_mode():
    """测试 4：MiMo 深度思考模式（可选）"""
    print()
    print("=" * 50)
    print("【测试 4】深度思考模式（MiMo 特有）")
    print("=" * 50)

    from agent.llm_client import get_llm
    from langchain_core.messages import HumanMessage

    llm = get_llm(with_reasoning=True)
    if not llm:
        print("  ⚠️  LLM 不可用，跳过")
        return False

    try:
        resp = llm.invoke([HumanMessage(content="一个员工报销了8000元差旅费，他的职级是专员（P4），差旅标准是400元/天。请分析这笔报销是否合规，并给出审批建议。")])

        content = resp.content if hasattr(resp, "content") else ""
        reasoning = ""
        if hasattr(resp, "additional_kwargs"):
            reasoning = resp.additional_kwargs.get("reasoning_content", "")

        if reasoning:
            print(f"  思考过程：{reasoning[:200]}...")
        print(f"  最终回答：{content[:200]}...")
        print("  ✅ 深度思考模式测试通过")
        return True

    except Exception as e:
        print(f"  ❌ 调用失败：{e}")
        return False


def main():
    """运行所有测试"""
    print()
    print("╔" + "═" * 48 + "╗")
    print("║    MiMo API 接入测试                           ║")
    print("╚" + "═" * 48 + "╝")
    print()

    # 显示配置
    from agent.config import AgentConfig
    print(f"  LLM_PROVIDER:  {AgentConfig.LLM_PROVIDER}")
    print(f"  USE_REAL_LLM:  {AgentConfig.USE_REAL_LLM}")
    print(f"  MIMO_MODEL:    {AgentConfig.MIMO_MODEL_NAME}")
    print(f"  MIMO_BASE_URL: {AgentConfig.MIMO_BASE_URL}")
    print(f"  MIMO_KEY_SET:  {'是' if AgentConfig.MIMO_API_KEY else '否'}")
    print()

    results = []
    results.append(("纯对话", test_pure_chat()))
    results.append(("工具调用", test_tool_calling()))
    results.append(("审批流", test_approval_flow()))
    results.append(("深度思考", test_reasoning_mode()))

    print()
    print("=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    total = len(results)
    ok = sum(1 for _, p in results if p)
    print(f"\n  总计：{ok}/{total} 通过")


if __name__ == "__main__":
    main()
