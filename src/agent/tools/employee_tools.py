# -*- coding: utf-8 -*-
"""
员工信息查询工具
================
封装员工信息查询，供 Agent 调用
"""

from langchain_core.tools import tool
from .base import find_employee, find_department, get_all_employees, get_levels


@tool
def get_employee_info(employee_id: int) -> dict:
    """查询员工基本信息，包括姓名、工号、部门、职级、角色"""
    emp = find_employee(employee_id)
    if not emp:
        return {"error": f"员工 {employee_id} 不存在"}
    dept = find_department(emp["dept_id"])
    levels = get_levels()
    lv_info = levels.get(emp["level"], {})
    return {
        "id": emp["id"],
        "name": emp["name"],
        "emp_no": emp["emp_no"],
        "department": dept["name"] if dept else "未知",
        "level": emp["level"],
        "level_name": lv_info.get("name", emp["level"]),
        "role": emp["role"],
    }


@tool
def get_employee_expense_limits(employee_id: int) -> dict:
    """查询员工职级对应的报销标准上限"""
    emp = find_employee(employee_id)
    if not emp:
        return {"error": f"员工 {employee_id} 不存在"}
    levels = get_levels()
    lv = levels.get(emp["level"], {})
    return {
        "employee": emp["name"],
        "level": emp["level"],
        "level_name": lv.get("name", ""),
        "limits": {
            "travel_per_day": lv.get("travel", 0),
            "meal_per_meal": lv.get("meal", 0),
            "transport_per_trip": lv.get("transport", 0),
        },
    }


@tool
def get_department_manager(department_id: int) -> dict:
    """查询部门经理信息"""
    dept = find_department(department_id)
    if not dept:
        return {"error": f"部门 {department_id} 不存在"}
    mgr = find_employee(dept["mgr"])
    return {
        "department": dept["name"],
        "manager_id": dept["mgr"],
        "manager_name": mgr["name"] if mgr else "未知",
    }
