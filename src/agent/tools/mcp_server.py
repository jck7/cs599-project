# -*- coding: utf-8 -*-
"""
MCP 服务端
==========
基于 MCP 协议统一封装所有业务工具
实现工具标准化接入与动态挂载
"""

from typing import Dict, Any, List, Callable, Optional
from datetime import datetime


class MCPTool:
    """MCP 工具定义"""

    def __init__(self, name: str, description: str, handler: Callable,
                 parameters: Optional[Dict] = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {}
        self.call_count = 0
        self.last_called_at: Optional[str] = None

    def invoke(self, **kwargs) -> Dict[str, Any]:
        """调用工具"""
        self.call_count += 1
        self.last_called_at = datetime.now().isoformat()
        try:
            result = self.handler(**kwargs)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def to_schema(self) -> Dict[str, Any]:
        """导出为 MCP 标准 Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class MCPServer:
    """
    MCP 协议服务端
    统一管理所有业务工具，支持动态注册与调用
    """

    def __init__(self, name: str = "oa-agent-mcp"):
        self.name = name
        self._tools: Dict[str, MCPTool] = {}
        self._call_log: List[Dict[str, Any]] = []

    def register_tool(self, name: str, description: str, handler: Callable,
                      parameters: Optional[Dict] = None) -> MCPTool:
        """注册工具"""
        tool = MCPTool(name, description, handler, parameters)
        self._tools[name] = tool
        return tool

    def unregister_tool(self, name: str):
        """注销工具"""
        self._tools.pop(name, None)

    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """调用指定工具"""
        tool = self._tools.get(tool_name)
        if not tool:
            return {"status": "error", "message": f"工具 {tool_name} 不存在"}

        start = datetime.now()
        result = tool.invoke(**kwargs)
        elapsed = (datetime.now() - start).total_seconds()

        self._call_log.append({
            "tool": tool_name,
            "args": kwargs,
            "result_status": result.get("status"),
            "elapsed_ms": round(elapsed * 1000, 1),
            "timestamp": datetime.now().isoformat(),
        })

        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有已注册工具"""
        return [t.to_schema() for t in self._tools.values()]

    def get_tool_stats(self) -> Dict[str, Any]:
        """获取工具调用统计"""
        return {
            "total_tools": len(self._tools),
            "total_calls": len(self._call_log),
            "tools": {
                name: {"calls": t.call_count, "last_called": t.last_called_at}
                for name, t in self._tools.items()
            },
        }

    def get_call_log(self, limit: int = 50) -> List[Dict]:
        """获取调用日志"""
        return self._call_log[-limit:]


# 全局 MCP 服务实例
mcp_server = MCPServer()


def register_all_tools():
    """注册所有业务工具到 MCP 服务"""
    from ..tools.employee_tools import get_employee_info, get_employee_expense_limits, get_department_manager
    from ..tools.budget_tools import get_department_budget, check_budget_affordable
    from ..tools.history_tools import get_employee_expense_history, detect_frequency_anomaly, detect_amount_spike
    from ..tools.rule_tools import get_approval_rule, check_expense_standard, get_expense_type_info

    tools = [
        (get_employee_info, "查询员工基本信息"),
        (get_employee_expense_limits, "查询员工报销标准上限"),
        (get_department_manager, "查询部门经理信息"),
        (get_department_budget, "查询部门年度预算"),
        (check_budget_affordable, "检查预算是否可承担"),
        (get_employee_expense_history, "查询员工报销历史"),
        (detect_frequency_anomaly, "检测报销频率异常"),
        (detect_amount_spike, "检测金额异常飙升"),
        (get_approval_rule, "查询审批流规则"),
        (check_expense_standard, "检查费用标准"),
        (get_expense_type_info, "获取费用类型信息"),
    ]

    for tool_fn, desc in tools:
        mcp_server.register_tool(
            name=tool_fn.name if hasattr(tool_fn, 'name') else tool_fn.__name__,
            description=desc,
            handler=tool_fn.invoke if hasattr(tool_fn, 'invoke') else tool_fn,
        )
