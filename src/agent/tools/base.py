# -*- coding: utf-8 -*-
"""
工具基类
========
封装与原始系统数据层的桥接逻辑
"""

import sys
from pathlib import Path

# 将 legacy_system 加入 Python 路径，以便导入其数据模块
_legacy_path = str(Path(__file__).resolve().parent.parent.parent / "legacy_system")
if _legacy_path not in sys.path:
    sys.path.insert(0, _legacy_path)


def get_legacy_data():
    """延迟导入原始系统数据（避免循环导入）"""
    import importlib
    # 重新加载以获取最新数据
    if "app" in sys.modules:
        mod = sys.modules["app"]
    else:
        # 动态导入
        import importlib.util
        spec = importlib.util.spec_from_file_location("legacy_app", Path(_legacy_path) / "app.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


def find_employee(emp_id: int) -> dict:
    """查找员工信息"""
    mod = get_legacy_data()
    return mod._find_emp(emp_id)


def find_department(dept_id: int) -> dict:
    """查找部门信息"""
    mod = get_legacy_data()
    return mod._find_dept(dept_id)


def get_all_expenses() -> list:
    """获取所有报销单"""
    mod = get_legacy_data()
    return mod.EXPENSES


def get_all_employees() -> list:
    """获取所有员工"""
    mod = get_legacy_data()
    return mod.EMPLOYEES


def get_budgets() -> dict:
    """获取预算数据"""
    mod = get_legacy_data()
    return mod.BUDGETS


def get_levels() -> dict:
    """获取职级标准"""
    mod = get_legacy_data()
    return mod.LEVELS


def get_expense_types() -> list:
    """获取费用类型"""
    mod = get_legacy_data()
    return mod.EXPENSE_TYPES
