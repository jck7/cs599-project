# -*- coding: utf-8 -*-
"""
传统 OA 报销管理系统 v2.0
========================
唯一启动入口，包含路由、模拟数据、业务接口、四级审批流
运行方式: pip install flask && python app.py
访问地址: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import random
import json

# ── 从 mock_data 模块导入所有数据 ──
from mock_data import (
    DEPARTMENTS, LEVELS, EXPENSE_TYPES, EMPLOYEES, EXPENSES, BUDGETS,
    NEXT_ID, STATUS_MAP, NODE_MAP, POLICY_DOCUMENTS,
    generate_expenses, init_budgets,
)

# ────────────────────────────────────────────────────────────
# 应用初始化
# ────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "oa-reimbursement-legacy-2024"


# ────────────────────────────────────────────────────────────
# Jinja 过滤器
# ────────────────────────────────────────────────────────────
@app.template_filter("dept_name")
def _dept_name(dept_id):
    d = _find_dept(dept_id)
    return d["name"] if d else "未知部门"

@app.template_filter("level_name")
def _level_name(level):
    return LEVELS.get(level, {}).get("name", level)

@app.template_filter("type_name")
def _type_name(code):
    for t in EXPENSE_TYPES:
        if t["code"] == code:
            return t["name"]
    return code

@app.template_filter("status_label")
def _status_label(status):
    return STATUS_MAP.get(status, status)

@app.template_filter("node_label")
def _node_label(node):
    return NODE_MAP.get(node, node)


# ────────────────────────────────────────────────────────────
# 辅助函数
# ────────────────────────────────────────────────────────────
def _find_emp(eid):
    for e in EMPLOYEES:
        if e["id"] == eid:
            return e
    return None

def _find_dept(did):
    for d in DEPARTMENTS:
        if d["id"] == did:
            return d
    return None

def _current_user():
    uid = session.get("user_id")
    return _find_emp(uid) if uid else None

def _approval_nodes(amount):
    nodes = [
        {"node": "dept_manager", "name": "部门经理审批"},
        {"node": "finance",      "name": "财务审核"},
    ]
    if amount >= 1000:
        nodes.append({"node": "finance_director", "name": "财务总监审批"})
    if amount >= 5000:
        nodes.append({"node": "ceo", "name": "总经理审批"})
    return nodes

def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _today_str():
    return datetime.now().strftime("%Y-%m-%d")


# ────────────────────────────────────────────────────────────
# 路由：登录 / 登出
# ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form.get("user_id")
        if uid:
            session["user_id"] = int(uid)
            return redirect(url_for("dashboard"))
    return render_template("login.html", employees=EMPLOYEES, departments=DEPARTMENTS)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ────────────────────────────────────────────────────────────
# 路由：数据看板
# ────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    now = datetime.now()
    cy, cm = now.year, now.month

    pending_cnt = 0
    for e in EXPENSES:
        if e["status"] != "pending":
            continue
        if user["role"] == "manager" and e["current_node"] == "dept_manager" and e["dept_id"] == user["dept_id"]:
            pending_cnt += 1
        elif user["role"] in ("finance", "finance_director") and e["current_node"] in ("finance", "finance_director"):
            pending_cnt += 1
        elif user["role"] == "ceo" and e["current_node"] == "ceo":
            pending_cnt += 1

    m_count, m_amount = 0, 0.0
    for e in EXPENSES:
        if e["applicant_id"] == user["id"] and e["submit_time"]:
            try:
                st = datetime.strptime(e["submit_time"], "%Y-%m-%d %H:%M:%S")
                if st.year == cy and st.month == cm:
                    m_count += 1
                    m_amount += e["amount"]
            except ValueError:
                pass

    b = BUDGETS.get((user["dept_id"], cy))
    b_rate = round((b["total"] - b["used"]) / b["total"] * 100, 1) if b and b["total"] > 0 else 0

    t_labels, t_values = [], []
    for i in range(5, -1, -1):
        m, y = cm - i, cy
        while m <= 0:
            m += 12; y -= 1
        t_labels.append(f"{y}-{m:02d}")
        t_values.append(round(sum(
            e["amount"] for e in EXPENSES
            if e["status"] in ("approved", "paid", "archived") and e["exp_date"][:7] == f"{y}-{m:02d}"
        ), 2))

    d_labels, d_values = [], []
    for dept in DEPARTMENTS:
        db = BUDGETS.get((dept["id"], cy))
        if db and db["total"] > 0:
            d_labels.append(dept["name"])
            d_values.append(round(db["used"] / db["total"] * 100, 1))

    my_pending = sorted(
        [e for e in EXPENSES if e["applicant_id"] == user["id"] and e["status"] in ("pending", "rejected")],
        key=lambda x: x["created"], reverse=True
    )[:10]

    recent = []
    for e in EXPENSES:
        if e["history"]:
            h = e["history"][-1]
            recent.append({"eid": e["id"], "title": e["title"], "act": h["label"], "op": h["op_name"], "time": h["time"]})
    recent.sort(key=lambda x: x["time"], reverse=True)

    return render_template("dashboard.html",
        user=user, pending_cnt=pending_cnt, m_count=m_count,
        m_amount=round(m_amount, 2), b_rate=b_rate,
        t_labels=json.dumps(t_labels), t_values=json.dumps(t_values),
        d_labels=json.dumps(d_labels), d_values=json.dumps(d_values),
        my_pending=my_pending, recent=recent[:15],
        _find_emp=_find_emp, _find_dept=_find_dept,
    )


# ────────────────────────────────────────────────────────────
# 路由：发起报销
# ────────────────────────────────────────────────────────────
@app.route("/apply", methods=["GET", "POST"])
def apply():
    global NEXT_ID
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        items_raw = request.form.get("items_json", "[]")
        att_raw = request.form.get("atts_json", "[]")
        action = request.form.get("action", "save")

        try:
            items = json.loads(items_raw)
        except (json.JSONDecodeError, TypeError):
            items = []
        try:
            atts = json.loads(att_raw)
        except (json.JSONDecodeError, TypeError):
            atts = []

        total = round(sum(float(it.get("amount", 0)) for it in items), 2)
        status = "draft" if action == "save" else "pending"
        now_s = _now_str()

        history = []
        cur_node = "submit"
        if status == "pending":
            history.append({
                "node": "submit", "name": "提交申请",
                "op_id": user["id"], "op_name": user["name"],
                "action": "submit", "label": "提交",
                "time": now_s, "comment": "报销申请已提交",
            })
            nodes = _approval_nodes(total)
            cur_node = nodes[0]["node"] if nodes else "dept_manager"

        detail = [{"type": it.get("type", "OTHER"), "amount": float(it.get("amount", 0)),
                    "date": it.get("date", ""), "reason": it.get("reason", "")} for it in items]

        EXPENSES.append({
            "id": NEXT_ID, "title": title, "applicant_id": user["id"],
            "dept_id": user["dept_id"], "amount": total, "status": status,
            "current_node": cur_node, "exp_date": detail[0]["date"] if detail else _today_str(),
            "submit_time": now_s if status == "pending" else None,
            "detail": detail, "attachments": atts,
            "nodes": _approval_nodes(total), "history": history, "created": now_s,
        })
        NEXT_ID += 1
        return jsonify({"code": 0, "message": "草稿保存成功" if action == "save" else "报销单已提交"})

    lv = LEVELS.get(user["level"], {})
    db = BUDGETS.get((user["dept_id"], datetime.now().year))
    return render_template("apply.html", user=user, types=EXPENSE_TYPES,
                           lv=lv, lv_name=LEVELS.get(user["level"], {}).get("name", ""),
                           db=db, _approval_nodes=_approval_nodes)


# ────────────────────────────────────────────────────────────
# 路由：我的报销
# ────────────────────────────────────────────────────────────
@app.route("/my_reimburse")
def my_reimburse():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    sf = request.args.get("status", "")
    kw = request.args.get("keyword", "")
    lst = [e for e in EXPENSES if e["applicant_id"] == user["id"]]
    if sf:
        lst = [e for e in lst if e["status"] == sf]
    if kw:
        lst = [e for e in lst if kw.lower() in e["title"].lower()]
    lst.sort(key=lambda x: x["created"], reverse=True)

    return render_template("my_reimburse.html", user=user, expenses=lst, sf=sf, kw=kw,
                           _find_emp=_find_emp, _find_dept=_find_dept)


# ────────────────────────────────────────────────────────────
# 路由：审批中心
# ────────────────────────────────────────────────────────────
@app.route("/approval")
def approval():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    tab = request.args.get("tab", "pending")
    if tab == "pending":
        plist = []
        for e in EXPENSES:
            if e["status"] != "pending":
                continue
            if user["role"] == "manager" and e["current_node"] == "dept_manager" and e["dept_id"] == user["dept_id"]:
                plist.append(e)
            elif user["role"] == "finance" and e["current_node"] == "finance":
                plist.append(e)
            elif user["role"] == "finance_director" and e["current_node"] == "finance_director":
                plist.append(e)
            elif user["role"] == "ceo" and e["current_node"] == "ceo":
                plist.append(e)
        plist.sort(key=lambda x: x.get("submit_time", ""), reverse=True)
        return render_template("approval.html", user=user, tab=tab, plist=plist, dlist=[],
                               _find_emp=_find_emp, _find_dept=_find_dept)
    else:
        dlist = []
        for e in EXPENSES:
            for h in e.get("history", []):
                if h["op_id"] == user["id"] and h["action"] in ("approve", "reject"):
                    dlist.append(e)
                    break
        dlist.sort(key=lambda x: x["created"], reverse=True)
        return render_template("approval.html", user=user, tab=tab, plist=[], dlist=dlist,
                               _find_emp=_find_emp, _find_dept=_find_dept)


# ────────────────────────────────────────────────────────────
# 路由：报销单详情
# ────────────────────────────────────────────────────────────
@app.route("/detail/<int:eid>")
def detail(eid):
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    exp = next((e for e in EXPENSES if e["id"] == eid), None)
    if not exp:
        return "报销单不存在", 404

    applicant = _find_emp(exp["applicant_id"])
    dept = _find_dept(exp["dept_id"])

    can_approve = False
    if exp["status"] == "pending":
        if user["role"] == "manager" and exp["current_node"] == "dept_manager" and exp["dept_id"] == user["dept_id"]:
            can_approve = True
        elif user["role"] == "finance" and exp["current_node"] == "finance":
            can_approve = True
        elif user["role"] == "finance_director" and exp["current_node"] == "finance_director":
            can_approve = True
        elif user["role"] == "ceo" and exp["current_node"] == "ceo":
            can_approve = True

    can_withdraw = (exp["applicant_id"] == user["id"] and exp["status"] == "pending")
    can_edit = (exp["applicant_id"] == user["id"] and exp["status"] in ("draft", "rejected"))
    can_pay = (exp["status"] == "approved" and user["role"] in ("finance", "finance_director"))
    lv_info = LEVELS.get(applicant["level"], {}) if applicant else {}

    return render_template("detail.html", user=user, exp=exp, applicant=applicant, dept=dept,
                           can_approve=can_approve, can_withdraw=can_withdraw,
                           can_edit=can_edit, can_pay=can_pay, lv_info=lv_info,
                           types=EXPENSE_TYPES, _find_emp=_find_emp, _find_dept=_find_dept)


# ────────────────────────────────────────────────────────────
# 路由：预算管理
# ────────────────────────────────────────────────────────────
@app.route("/budget")
def budget():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    year = int(request.args.get("year", datetime.now().year))
    bdata = []
    for dept in DEPARTMENTS:
        b = BUDGETS.get((dept["id"], year), {"total": 0, "used": 0})
        remain = b["total"] - b["used"]
        rate = round(b["used"] / b["total"] * 100, 1) if b["total"] > 0 else 0
        bdata.append({"dept": dept, "total": b["total"], "used": round(b["used"], 2),
                      "remain": round(remain, 2), "rate": rate, "over": b["used"] > b["total"]})

    t_labels = [f"{m}月" for m in range(1, 13)]
    t_data = {}
    for dept in DEPARTMENTS:
        monthly = [round(sum(
            e["amount"] for e in EXPENSES
            if e["dept_id"] == dept["id"] and e["status"] in ("approved", "paid", "archived")
            and e["exp_date"][:7] == f"{year}-{m:02d}"
        ), 2) for m in range(1, 13)]
        t_data[dept["name"]] = monthly

    return render_template("budget.html", user=user, bdata=bdata, year=year,
                           t_labels=json.dumps(t_labels), t_data=json.dumps(t_data), depts=DEPARTMENTS)


# ────────────────────────────────────────────────────────────
# 路由：费用标准
# ────────────────────────────────────────────────────────────
@app.route("/rule")
def rule():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("rule.html", user=user, levels=LEVELS, types=EXPENSE_TYPES)


# ────────────────────────────────────────────────────────────
# 路由：员工管理
# ────────────────────────────────────────────────────────────
@app.route("/employee")
def employee():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    kw = request.args.get("keyword", "")
    df = request.args.get("dept", "")
    elist = EMPLOYEES[:]
    if kw:
        elist = [e for e in elist if kw.lower() in e["name"].lower() or kw.lower() in e["emp_no"].lower()]
    if df:
        elist = [e for e in elist if str(e["dept_id"]) == df]

    return render_template("employee.html", user=user, employees=elist,
                           departments=DEPARTMENTS, levels=LEVELS, kw=kw, df=df, _find_dept=_find_dept)


# ────────────────────────────────────────────────────────────
# API：审批通过 / 驳回
# ────────────────────────────────────────────────────────────
@app.route("/api/approve", methods=["POST"])
def api_approve():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})

    data = request.get_json()
    eid = data.get("id")
    action = data.get("action")
    comment = data.get("comment", "")

    if action == "reject" and not comment.strip():
        return jsonify({"code": 400, "message": "驳回必须填写意见"})

    exp = next((e for e in EXPENSES if e["id"] == eid), None)
    if not exp:
        return jsonify({"code": 404, "message": "报销单不存在"})
    if exp["status"] != "pending":
        return jsonify({"code": 400, "message": "该单据不在审批流程中"})

    now_s = _now_str()
    exp["history"].append({
        "node": exp["current_node"], "name": NODE_MAP.get(exp["current_node"], ""),
        "op_id": user["id"], "op_name": user["name"],
        "action": action, "label": "通过" if action == "approve" else "驳回",
        "time": now_s, "comment": comment or "同意",
    })

    if action == "reject":
        exp["status"] = "rejected"
        exp["current_node"] = "submit"
        return jsonify({"code": 0, "message": "已驳回"})

    nodes = exp["nodes"]
    idx = next((i for i, n in enumerate(nodes) if n["node"] == exp["current_node"]), -1)
    if idx < len(nodes) - 1:
        exp["current_node"] = nodes[idx + 1]["node"]
    else:
        exp["status"] = "approved"
        exp["current_node"] = "payment"
        year = int(exp["exp_date"][:4])
        bk = (exp["dept_id"], year)
        if bk in BUDGETS:
            BUDGETS[bk]["used"] = round(BUDGETS[bk]["used"] + exp["amount"], 2)

    return jsonify({"code": 0, "message": "审批通过"})


# ────────────────────────────────────────────────────────────
# API：撤回
# ────────────────────────────────────────────────────────────
@app.route("/api/withdraw", methods=["POST"])
def api_withdraw():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})

    eid = request.get_json().get("id")
    for e in EXPENSES:
        if e["id"] == eid and e["applicant_id"] == user["id"] and e["status"] == "pending":
            e["status"] = "draft"
            e["current_node"] = "submit"
            e["history"].append({
                "node": "submit", "name": "撤回",
                "op_id": user["id"], "op_name": user["name"],
                "action": "withdraw", "label": "撤回",
                "time": _now_str(), "comment": "申请人撤回",
            })
            return jsonify({"code": 0, "message": "已撤回"})
    return jsonify({"code": 400, "message": "操作失败"})


# ────────────────────────────────────────────────────────────
# API：打款
# ────────────────────────────────────────────────────────────
@app.route("/api/pay", methods=["POST"])
def api_pay():
    user = _current_user()
    if not user or user["role"] not in ("finance", "finance_director"):
        return jsonify({"code": 403, "message": "无权限"})

    eid = request.get_json().get("id")
    for e in EXPENSES:
        if e["id"] == eid and e["status"] == "approved":
            e["status"] = "paid"
            e["history"].append({
                "node": "payment", "name": "财务打款",
                "op_id": user["id"], "op_name": user["name"],
                "action": "pay", "label": "已打款",
                "time": _now_str(), "comment": "款项已转账",
            })
            return jsonify({"code": 0, "message": "打款成功"})
    return jsonify({"code": 400, "message": "操作失败"})


# ────────────────────────────────────────────────────────────
# API：批量审批
# ────────────────────────────────────────────────────────────
@app.route("/api/batch_approve", methods=["POST"])
def api_batch_approve():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})

    data = request.get_json()
    ids = data.get("ids", [])
    comment = data.get("comment", "批量审批通过")
    cnt = 0

    for eid in ids:
        exp = next((e for e in EXPENSES if e["id"] == eid and e["status"] == "pending"), None)
        if not exp:
            continue
        can = False
        if user["role"] == "manager" and exp["current_node"] == "dept_manager" and exp["dept_id"] == user["dept_id"]:
            can = True
        elif user["role"] == "finance" and exp["current_node"] == "finance":
            can = True
        elif user["role"] == "finance_director" and exp["current_node"] == "finance_director":
            can = True
        elif user["role"] == "ceo" and exp["current_node"] == "ceo":
            can = True

        if can:
            now_s = _now_str()
            exp["history"].append({
                "node": exp["current_node"], "name": NODE_MAP.get(exp["current_node"], ""),
                "op_id": user["id"], "op_name": user["name"],
                "action": "approve", "label": "通过",
                "time": now_s, "comment": comment,
            })
            nodes = exp["nodes"]
            idx = next((i for i, n in enumerate(nodes) if n["node"] == exp["current_node"]), -1)
            if idx < len(nodes) - 1:
                exp["current_node"] = nodes[idx + 1]["node"]
            else:
                exp["status"] = "approved"
                exp["current_node"] = "payment"
                year = int(exp["exp_date"][:4])
                bk = (exp["dept_id"], year)
                if bk in BUDGETS:
                    BUDGETS[bk]["used"] = round(BUDGETS[bk]["used"] + exp["amount"], 2)
            cnt += 1

    return jsonify({"code": 0, "message": f"成功审批 {cnt} 条"})


# ────────────────────────────────────────────────────────────
# API：重新提交
# ────────────────────────────────────────────────────────────
@app.route("/api/resubmit", methods=["POST"])
def api_resubmit():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})

    data = request.get_json()
    eid = data.get("id")
    for e in EXPENSES:
        if e["id"] == eid and e["applicant_id"] == user["id"] and e["status"] == "rejected":
            now_s = _now_str()
            e["status"] = "pending"
            e["nodes"] = _approval_nodes(e["amount"])
            e["current_node"] = e["nodes"][0]["node"] if e["nodes"] else "dept_manager"
            e["submit_time"] = now_s
            e["history"].append({
                "node": "submit", "name": "重新提交",
                "op_id": user["id"], "op_name": user["name"],
                "action": "resubmit", "label": "重新提交",
                "time": now_s, "comment": "修改后重新提交",
            })
            return jsonify({"code": 0, "message": "已重新提交"})
    return jsonify({"code": 400, "message": "操作失败"})


# ────────────────────────────────────────────────────────────
# API：获取报销单 JSON
# ────────────────────────────────────────────────────────────
@app.route("/api/expense/<int:eid>")
def api_expense(eid):
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})

    exp = next((e for e in EXPENSES if e["id"] == eid), None)
    if not exp:
        return jsonify({"code": 404, "message": "不存在"})

    emp = _find_emp(exp["applicant_id"])
    return jsonify({"code": 0, "data": {
        **exp,
        "applicant_name": emp["name"] if emp else "未知",
        "dept_name": (_find_dept(exp["dept_id"]) or {}).get("name", ""),
        "status_label": STATUS_MAP.get(exp["status"], exp["status"]),
        "level_name": LEVELS.get(emp["level"], {}).get("name", "") if emp else "",
    }})


# ════════════════════════════════════════════════════════════
# 以下为 AI 智能化改造新增代码段（不修改原有业务逻辑）
# ════════════════════════════════════════════════════════════

import sys
from pathlib import Path as _Path

_agent_root = str(_Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

_ai_service = None

def _get_ai_service():
    global _ai_service
    if _ai_service is None:
        try:
            from agent.service import agent_service
            _ai_service = agent_service
        except ImportError as e:
            _ai_service = {"error": str(e)}
    return _ai_service


@app.route("/debug/qa/<question>")
def debug_qa(question):
    user = _current_user()
    if not user:
        return redirect(url_for("login"))

    try:
        from agent.llm import llm_client
        version = getattr(llm_client, '_CODE_VERSION', 'unknown')
    except Exception:
        version = 'import_error'

    from agent.config import AgentConfig as _cfg
    cfg_info = f"USE_REAL_LLM={_cfg.USE_REAL_LLM}, PROVIDER={_cfg.LLM_PROVIDER}, KEY={'set' if _cfg.MIMO_API_KEY else 'empty'}"

    init_test = ""
    init_error = ""
    try:
        from agent.llm.llm_client import get_llm
        llm_instance = get_llm()
        init_test = f"type={type(llm_instance).__name__}" if llm_instance else "None"
    except Exception as e:
        init_test = "exception"
        init_error = str(e)

    svc = _get_ai_service()
    qa_result = "not_tested"
    if not (isinstance(svc, dict) and "error" in svc):
        try:
            result = svc.ask_question(question=question, user_id=user["id"], user_level=user.get("level", ""))
            qa_result = f"llm_used={result.get('llm_used')}, model={result.get('model_name')}"
        except Exception as e:
            qa_result = f"error: {e}"

    return f"""<pre>
Code Version: {version}
Config: {cfg_info}
LLM Init: {init_test}
Init Error: {init_error}
QA Result: {qa_result}
</pre>"""


@app.route("/debug/reset")
def debug_reset():
    try:
        from agent.llm.llm_client import _exit_fallback
        _exit_fallback()
        return "<pre>Fallback state reset.</pre>"
    except Exception as e:
        return f"<pre>Error: {e}</pre>"


@app.route("/api/ai/status")
def api_ai_status():
    try:
        from agent.config import AgentConfig
        from agent.llm.llm_client import is_fallback_active, get_fallback_info
        provider = AgentConfig.LLM_PROVIDER
        active = "none"
        if AgentConfig.USE_REAL_LLM:
            if provider == "mimo" and AgentConfig.MIMO_API_KEY:
                active = "mimo"
            elif provider == "deepseek" and AgentConfig.DEEPSEEK_API_KEY:
                active = "deepseek"
            elif provider == "auto":
                if AgentConfig.MIMO_API_KEY:
                    active = "mimo"
                elif AgentConfig.DEEPSEEK_API_KEY:
                    active = "deepseek"
        fb = get_fallback_info()
        return jsonify({"code": 0, "data": {
            "llm_enabled": AgentConfig.USE_REAL_LLM,
            "provider": provider, "active": active,
            "fallback_active": fb["fallback_active"],
            "fallback_reason": fb["fallback_reason"],
        }})
    except Exception:
        return jsonify({"code": 0, "data": {"llm_enabled": False, "provider": "none", "active": "none", "fallback_active": False, "fallback_reason": ""}})


@app.route("/api/ai/analyze/<int:eid>")
def api_ai_analyze(eid):
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})
    svc = _get_ai_service()
    if isinstance(svc, dict) and "error" in svc:
        return jsonify({"code": 503, "message": f"AI 服务不可用: {svc['error']}"})
    try:
        result = svc.analyze_expense(eid)
        if "error" in result and result.get("error") and not result.get("final_decision"):
            return jsonify({"code": 404, "message": result["error"]})
        return jsonify({"code": 0, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "message": f"分析失败: {str(e)}"})


@app.route("/ai/dashboard")
def ai_dashboard():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))
    svc = _get_ai_service()
    stats = {"total_processed": 0, "auto_approved": 0, "auto_rejected": 0,
             "manual_review": 0, "auto_rate": 0, "avg_process_time_sec": 0,
             "risk_intercepted": 0, "human_intervention_rate": 0}
    if not (isinstance(svc, dict) and "error" in svc):
        try:
            stats = svc.get_dashboard_stats()
        except Exception:
            pass
    high_risk = [e for e in EXPENSES if e["status"] == "pending" and e["amount"] >= 2000][:10]
    return render_template("ai_dashboard.html", user=user, stats=stats, high_risk=high_risk,
        _find_emp=_find_emp, _find_dept=_find_dept)


@app.route("/ai/comparison")
def ai_comparison():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))
    total = len([e for e in EXPENSES if e["status"] != "draft"])
    approved = len([e for e in EXPENSES if e["status"] in ("approved", "paid", "archived")])
    rejected = len([e for e in EXPENSES if e["status"] == "rejected"])
    comparison = {
        "before": {"avg_time_hours": 48, "manual_ratio": 100, "compliance_rate": 75, "budget_response_hours": 24},
        "after": {"avg_time_hours": 2, "manual_ratio": 35, "compliance_rate": 95, "budget_response_hours": 0.1},
        "data": {"total_expenses": total, "approved": approved, "rejected": rejected},
    }
    return render_template("ai_comparison.html", user=user, comp=comparison)


@app.route("/ai/audit")
def ai_audit():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("ai_audit.html", user=user)


@app.route("/ai/qa")
def ai_qa():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("ai_qa.html", user=user)


@app.route("/ai/analysis")
def ai_analysis():
    user = _current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("ai_analysis.html", user=user)


@app.route("/api/ai/fill_assist", methods=["POST"])
def api_ai_fill_assist():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})
    svc = _get_ai_service()
    if isinstance(svc, dict) and "error" in svc:
        return jsonify({"code": 503, "message": "AI 服务不可用"})
    data = request.get_json()
    try:
        result = svc.get_fill_assistance(employee_id=user["id"], text=data.get("text", ""), current_items=data.get("items", []))
        return jsonify({"code": 0, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})


@app.route("/api/ai/audit", methods=["POST"])
def api_ai_audit():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})
    svc = _get_ai_service()
    if isinstance(svc, dict) and "error" in svc:
        return jsonify({"code": 503, "message": "AI 服务不可用"})
    data = request.get_json()
    try:
        result = svc.run_compliance_audit(days=data.get("days", 30), risk_level=data.get("risk_level", "all"))
        return jsonify({"code": 0, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})


@app.route("/api/ai/qa", methods=["POST"])
def api_ai_qa():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})
    svc = _get_ai_service()
    if isinstance(svc, dict) and "error" in svc:
        return jsonify({"code": 503, "message": "AI 服务不可用"})
    data = request.get_json()
    try:
        result = svc.ask_question(
            question=data.get("question", ""),
            user_id=user["id"],
            user_level=user.get("level", ""),
            user_dept=user.get("dept_id", ""),
            history=data.get("history", []),
        )
        return jsonify({"code": 0, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})


@app.route("/api/ai/qa/stream", methods=["POST"])
def api_ai_qa_stream():
    from flask import Response
    import json as _json

    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})

    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"code": 400, "message": "问题不能为空"})

    _FINANCE_KW = frozenset([
        "报销", "差旅", "出差", "餐饮", "交通", "住宿", "发票", "审批",
        "预算", "额度", "标准", "流程", "制度", "规定", "招待", "培训",
        "办公", "打款", "归档", "驳回", "撤回", "超标", "合规", "费用",
    ])
    is_finance = any(kw in question for kw in _FINANCE_KW)

    rag_context = ""
    sources = []
    if is_finance:
        try:
            from agent.knowledge.policy_kb import policy_kb
            results = policy_kb.search(question, top_k=3)
            if results and results[0].get("score", 0) > 0.15:
                rag_context = "\n".join([r["content"] for r in results])
                sources = [{"content": r["content"][:100] + "...", "score": r["score"]} for r in results]
        except Exception:
            pass

    if is_finance and rag_context:
        prompt = f"你是企业财务报销制度专家。请结合参考资料回答。\n参考资料：\n{rag_context}\n问题：{question}\n请回答："
    elif is_finance:
        prompt = f"你是企业财务报销制度专家。知识库无相关内容，请用专业知识回答。\n问题：{question}\n请回答："
    else:
        prompt = f"请直接回答：{question}"

    def generate():
        from agent.llm.llm_client import chat_stream
        from langchain_core.messages import HumanMessage

        meta = {"type": "meta", "sources": sources}
        yield f"data: {_json.dumps(meta, ensure_ascii=False)}\n\n"

        for chunk in chat_stream([HumanMessage(content=prompt)], scene="qa"):
            if chunk.get("chunk"):
                yield f"data: {_json.dumps({'type': 'chunk', 'content': chunk['chunk']}, ensure_ascii=False)}\n\n"
            if chunk.get("done"):
                llm_used = "rag_enhanced" if (is_finance and rag_context) else chunk.get("source", "unknown")
                yield f"data: {_json.dumps({'type': 'done', 'llm_used': llm_used}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/ai/analysis", methods=["POST"])
def api_ai_analysis():
    user = _current_user()
    if not user:
        return jsonify({"code": 401, "message": "未登录"})
    svc = _get_ai_service()
    if isinstance(svc, dict) and "error" in svc:
        return jsonify({"code": 503, "message": "AI 服务不可用"})
    data = request.get_json()
    try:
        result = svc.analyze_data(data.get("query", ""))
        return jsonify({"code": 0, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})


# ────────────────────────────────────────────────────────────
# 启动
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  企业报销管理系统 v2.0（含 AI 智能审批）")
    print("  访问地址: http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=True, host="127.0.0.1", port=5000)
