# -*- coding: utf-8 -*-
"""
内置测试用例
============
5 个典型场景，可一键演示 AI 审批效果
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def run_test_cases():
    """运行 5 个典型测试用例"""
    from agent.service import agent_service

    test_cases = [
        {"id": 1, "name": "正常通过", "desc": "低风险、小额、信息完整，预期自动通过"},
        {"id": 2, "name": "信息缺失", "desc": "草稿状态，信息不完整，预期驳回补充"},
        {"id": 3, "name": "预算超支", "desc": "部门预算紧张，预期风险提示"},
        {"id": 4, "name": "高风险", "desc": "高频报销+高额单据，预期转人工"},
        {"id": 5, "name": "大额转人工", "desc": "5000元以上，预期转高管审批"},
    ]

    # 选择具体的 expense_id 来匹配场景
    from agent.tools.base import get_all_expenses
    expenses = get_all_expenses()

    # 按场景匹配
    scenario_ids = {
        1: None,  # 低风险小额 approved
        2: None,  # draft
        3: None,  # 接近超预算
        4: None,  # 高频申请人
        5: None,  # 5000+
    }

    for e in expenses:
        amt = e["amount"]
        status = e["status"]
        if scenario_ids[1] is None and status == "approved" and amt < 500:
            scenario_ids[1] = e["id"]
        if scenario_ids[2] is None and status == "draft":
            scenario_ids[2] = e["id"]
        if scenario_ids[3] is None and status == "pending" and amt > 1000:
            scenario_ids[3] = e["id"]
        if scenario_ids[4] is None and status == "rejected":
            scenario_ids[4] = e["id"]
        if scenario_ids[5] is None and amt >= 5000:
            scenario_ids[5] = e["id"]

    print("=" * 60)
    print("  智能审批 Agent 测试用例演示")
    print("=" * 60)

    for tc in test_cases:
        eid = scenario_ids.get(tc["id"])
        if not eid:
            print(f"\n【用例 {tc['id']}】{tc['name']} - 未找到匹配单据")
            continue

        print(f"\n{'─' * 50}")
        print(f"【用例 {tc['id']}】{tc['name']}")
        print(f"  说明：{tc['desc']}")
        print(f"  报销单ID：{eid}")

        result = agent_service.analyze_expense(eid)

        if "error" in result and result.get("error") and not result.get("final_decision"):
            print(f"  ❌ 错误：{result['error']}")
            continue

        # 信息校验
        info = result.get("info_check", {})
        print(f"  📋 信息校验：{'通过' if info.get('passed') else '不通过'} - {info.get('message', '')}")

        # 预算校验
        budget = result.get("budget_check", {})
        print(f"  💰 预算校验：{'通过' if budget.get('passed') else '不通过'} - {budget.get('message', '')}")

        # 风险分析
        risk = result.get("risk_analysis", {})
        print(f"  ⚠️  风险评分：{risk.get('risk_score', 0)}/100（{risk.get('risk_level', '')}）")

        # 最终决策
        decision = result.get("final_decision", {})
        conclusion_map = {
            "auto_approve": "✅ 自动通过",
            "auto_reject": "❌ 自动驳回",
            "manual_review": "👤 转人工",
            "error": "⚠️ 异常",
        }
        print(f"  🤖 AI 决策：{conclusion_map.get(decision.get('conclusion', ''), decision.get('conclusion', ''))}")
        print(f"  📝 审批建议：{decision.get('approval_advice', '')}")

    print(f"\n{'=' * 60}")
    print("  测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_test_cases()
