# -*- coding: utf-8 -*-
"""
模拟业务数据初始化模块
======================
生成高度真实、逻辑自洽的企业级 OA 报销数据
覆盖 10 部门、60 员工、200+ 报销单、完整审批历史

文件路径：src/legacy_system/mock_data.py
"""

import random
from datetime import datetime, timedelta

random.seed(42)  # 保证每次重启数据一致

# ════════════════════════════════════════════════════════════
# 一、部门数据（11个部门）
# ════════════════════════════════════════════════════════════
DEPARTMENTS = [
    {"id": 1,  "name": "总经办",     "code": "CEO",   "budget": 500000},
    {"id": 2,  "name": "销售一部",   "code": "SALE1", "budget": 1000000},
    {"id": 3,  "name": "销售二部",   "code": "SALE2", "budget": 800000},
    {"id": 4,  "name": "市场部",     "code": "MKT",   "budget": 1200000},
    {"id": 5,  "name": "技术研发部", "code": "TECH",  "budget": 800000},
    {"id": 6,  "name": "产品部",     "code": "PROD",  "budget": 400000},
    {"id": 7,  "name": "运营部",     "code": "OPS",   "budget": 400000},
    {"id": 8,  "name": "财务部",     "code": "FIN",   "budget": 300000},
    {"id": 9,  "name": "人力资源部", "code": "HR",    "budget": 250000},
    {"id": 10, "name": "行政部",     "code": "ADM",   "budget": 200000},
    {"id": 11, "name": "法务部",     "code": "LEG",   "budget": 200000},
]

# ════════════════════════════════════════════════════════════
# 二、职级体系（5级）
# ════════════════════════════════════════════════════════════
LEVELS = {
    "P1": {"name": "专员",   "travel": 260, "meal": 100, "transport": 80},
    "P2": {"name": "主管",   "travel": 260, "meal": 120, "transport": 100},
    "M1": {"name": "经理",   "travel": 350, "meal": 150, "transport": 120},
    "M2": {"name": "总监",   "travel": 500, "meal": 200, "transport": 150},
    "M3": {"name": "总经理", "travel": 9999, "meal": 9999, "transport": 9999},
}

# ════════════════════════════════════════════════════════════
# 三、费用类型
# ════════════════════════════════════════════════════════════
EXPENSE_TYPES = [
    {"code": "TRAVEL",    "name": "差旅费",     "icon": "✈️"},
    {"code": "ENTERTAIN", "name": "业务招待费", "icon": "🤝"},
    {"code": "OFFICE",    "name": "办公采购费", "icon": "📎"},
    {"code": "TRANSPORT", "name": "市内交通费", "icon": "🚕"},
    {"code": "TELECOM",   "name": "通讯补贴",   "icon": "📱"},
    {"code": "OTHER",     "name": "其他费用",   "icon": "📦"},
]

# ════════════════════════════════════════════════════════════
# 四、状态映射
# ════════════════════════════════════════════════════════════
STATUS_MAP = {
    "draft": "草稿", "pending": "审批中", "approved": "已通过",
    "rejected": "已驳回", "paid": "已打款", "archived": "已归档",
}

NODE_MAP = {
    "submit": "提交申请", "dept_manager": "部门经理审批",
    "finance": "财务审核", "finance_director": "财务总监审批",
    "ceo": "总经理审批", "payment": "财务打款", "archive": "归档",
}

# ════════════════════════════════════════════════════════════
# 五、员工数据（60人）
# ════════════════════════════════════════════════════════════
def build_employees():
    """构建60名员工"""
    raw = [
        # 总经办 (1人)
        ("王建国", 1, "M3", "ceo",    "2020-01-01"),
        # 销售一部 (19人)
        ("李明辉", 2, "M2", "manager", "2021-03-15"),
        ("张伟东", 2, "M1", "manager", "2021-06-01"),
        ("刘强生", 2, "M1", "manager", "2022-01-10"),
        ("陈晓峰", 2, "P2", "employee","2022-03-01"),
        ("赵文博", 2, "P2", "employee","2022-04-15"),
        ("周志远", 2, "P2", "employee","2022-06-01"),
        ("吴佳明", 2, "P2", "employee","2022-08-15"),
        ("孙浩然", 2, "P1", "employee","2023-01-10"),
        ("马天宇", 2, "P1", "employee","2023-02-15"),
        ("朱俊杰", 2, "P1", "employee","2023-03-20"),
        ("胡文斌", 2, "P1", "employee","2023-05-01"),
        ("高志强", 2, "P1", "employee","2023-07-15"),
        ("林建华", 2, "P1", "employee","2023-09-01"),
        ("何小龙", 2, "P1", "employee","2024-01-10"),
        ("罗明阳", 2, "P1", "employee","2024-03-01"),
        ("梁天翔", 2, "P1", "employee","2024-05-15"),
        ("宋文杰", 2, "P1", "employee","2024-07-01"),
        ("唐浩宇", 2, "P1", "employee","2024-09-15"),
        # 销售二部 (15人)
        ("韩志远", 3, "M2", "manager", "2021-05-01"),
        ("冯建华", 3, "M1", "manager", "2022-02-15"),
        ("曹文博", 3, "P2", "employee","2022-05-01"),
        ("彭浩然", 3, "P2", "employee","2022-07-15"),
        ("潘天宇", 3, "P2", "employee","2022-09-01"),
        ("董俊杰", 3, "P1", "employee","2023-01-15"),
        ("袁文斌", 3, "P1", "employee","2023-04-01"),
        ("蒋志强", 3, "P1", "employee","2023-06-15"),
        ("沈建华", 3, "P1", "employee","2023-08-01"),
        ("韦小龙", 3, "P1", "employee","2024-01-15"),
        ("方明阳", 3, "P1", "employee","2024-04-01"),
        ("邱天翔", 3, "P1", "employee","2024-06-15"),
        ("田文杰", 3, "P1", "employee","2024-08-01"),
        ("石浩宇", 3, "P1", "employee","2024-10-15"),
        # 市场部 (9人)
        ("谢明辉", 4, "M2", "manager", "2021-04-01"),
        ("邹伟东", 4, "M1", "manager", "2022-01-15"),
        ("熊晓峰", 4, "P2", "employee","2022-06-01"),
        ("秦志远", 4, "P2", "employee","2023-01-15"),
        ("江浩然", 4, "P1", "employee","2023-05-01"),
        ("薛天宇", 4, "P1", "employee","2023-09-15"),
        ("侯俊杰", 4, "P1", "employee","2024-02-01"),
        ("龙文斌", 4, "P1", "employee","2024-06-15"),
        ("万志强", 4, "P1", "employee","2024-10-01"),
        # 技术研发部 (15人)
        ("段志远", 5, "M2", "manager", "2021-02-01"),
        ("雷浩然", 5, "M1", "manager", "2021-08-15"),
        ("常晓峰", 5, "P2", "employee","2022-01-01"),
        ("贺文博", 5, "P2", "employee","2022-04-15"),
        ("龚天宇", 5, "P2", "employee","2022-07-01"),
        ("武俊杰", 5, "P1", "employee","2022-10-15"),
        ("钱文斌", 5, "P1", "employee","2023-01-01"),
        ("戴志强", 5, "P1", "employee","2023-04-15"),
        ("严建华", 5, "P1", "employee","2023-07-01"),
        ("叶小龙", 5, "P1", "employee","2023-10-15"),
        ("余明阳", 5, "P1", "employee","2024-01-01"),
        ("苏天翔", 5, "P1", "employee","2024-04-15"),
        ("卢文杰", 5, "P1", "employee","2024-07-01"),
        # 产品部 (4人)
        ("丁浩宇", 6, "M1", "manager", "2021-09-01"),
        ("魏明辉", 6, "P2", "employee","2022-06-15"),
        ("任伟东", 6, "P1", "employee","2023-03-01"),
        ("姜晓峰", 6, "P1", "employee","2024-01-15"),
        # 运营部 (4人)
        ("钟志远", 7, "M1", "manager", "2021-11-01"),
        ("姚浩然", 7, "P2", "employee","2022-08-15"),
        ("康文博", 7, "P1", "employee","2023-05-01"),
        ("崔天宇", 7, "P1", "employee","2024-02-15"),
        # 财务部 (3人)
        ("秦丽华", 8, "M2", "finance_director", "2021-01-01"),
        ("王秀英", 8, "P2", "finance",          "2021-06-15"),
        ("李桂芳", 8, "P1", "finance",          "2022-03-01"),
        # 人力资源部 (3人)
        ("张春梅", 9, "M1", "manager", "2021-04-01"),
        ("刘美玲", 9, "P2", "employee","2022-07-15"),
        ("陈淑芬", 9, "P1", "employee","2023-04-01"),
        # 行政部 (3人)
        ("杨国庆", 10, "M1", "manager", "2021-05-01"),
        ("黄海燕", 10, "P2", "employee","2022-09-15"),
        ("吴丽萍", 10, "P1", "employee","2023-06-01"),
        # 法务部 (2人)
        ("郑大伟", 11, "M1", "manager", "2021-07-01"),
        ("林小燕", 11, "P1", "employee","2023-01-15"),
        # 管理员
        ("系统管理员", 10, "M2", "admin", "2020-01-01"),
    ]

    employees = []
    for i, (name, did, lv, role, join) in enumerate(raw, 1):
        employees.append({
            "id": i, "name": name, "emp_no": f"EMP2026{i:03d}",
            "dept_id": did, "level": lv, "role": role,
            "join_date": join, "phone": f"138{i:08d}",
            "email": f"{name.lower().replace(' ','')}@techcorp.com",
        })
    return employees


# ════════════════════════════════════════════════════════════
# 六、费用标准规则（支撑知识库问答）
# ════════════════════════════════════════════════════════════
POLICY_DOCUMENTS = [
    "差旅住宿标准：总经理实报实销，总监不超过500元/天，经理不超过350元/天，主管/专员不超过260元/天。超出标准需部门总监特批。",
    "交通标准：总监及以上可乘高铁一等座，经理及以下乘高铁二等座。800公里以内优先高铁，800公里以上可乘飞机经济舱。",
    "餐饮补助标准：出差期间总经理实报实销，总监200元/天，经理150元/天，主管/专员100元/天。商务宴请需事前审批。",
    "业务招待费标准：单次招待不超过3000元，需注明招待对象、人数、事由。全年招待费不超过部门预算的15%。",
    "市内交通费标准：总监及以上可乘出租车，主管/专员优先公共交通。每月25日前提交当月交通费报销。",
    "通讯补贴标准：总监300元/月，经理200元/月，主管/专员100元/月。按季度统一报销。",
    "报销发票要求：发票抬头必须是公司全称，税号完整。增值税专用发票需在30日内认证。电子发票需打印纸质版。",
    "报销发票真伪：财务部门有权对所有发票进行真伪查验。虚假发票一经发现，报销人需退回全部款项并接受纪律处分。",
    "报销发票粘贴：发票需按类别分组粘贴在报销粘贴单上，每张发票不得遮挡金额和税号。",
    "报销提交时限：出差返回后7个工作日内必须提交报销申请，逾期不予受理。",
    "报销审批流程（1000元以下）：员工提交→部门经理审批→财务审核→完成。预计1-2个工作日。",
    "报销审批流程（1000-5000元）：员工提交→部门经理→财务→财务总监→完成。预计2-3个工作日。",
    "报销审批流程（5000元以上）：员工提交→部门经理→财务→财务总监→总经理→完成。预计3-5个工作日。",
    "报销驳回处理：审批人驳回时必须填写驳回理由。申请人可修改后重新提交，保留完整审批历史。",
    "预算管理规定：每年12月编制下年度预算，经总经理审批后执行。按季度分解，超预算需提前申请追加。",
    "预算使用监控：财务部每月出具预算使用报告。使用率超80%预警，超100%冻结非必要报销。",
    "培训费报销：需提供培训通知、发票、培训心得。外部培训需事前经HR和部门经理审批。",
    "团建费报销：部门团建每人每次不超过500元，需提前申请。全年团建费不超过部门预算10%。",
    "预借差旅费：出差前可申请预借差旅费，金额不超过预算标准的80%。返回后5个工作日内核销。",
    "跨部门报销：费用归属多个部门时，需各相关部门经理会签。",
    "紧急报销：因特殊原因需紧急处理的报销，可走加急通道，财务部应在1个工作日内完成审核。",
    "历史报销查询：员工可通过系统查询近2年的报销记录。超过2年的记录需向财务部申请调阅。",
    "报销单据编号规则：单据编号格式为 R+年月+序号，如 R202601-001。",
    "打款周期：已通过的报销单在每周三统一打款，节假日顺延。",
    "归档规则：已打款的报销单在打款后30天自动归档，归档后不可修改。",
    "预算追加流程：部门经理提交预算追加申请→财务部审核→总经理审批→调整预算。",
    "费用类型分类：差旅费、业务招待费、办公采购费、市内交通费、通讯补贴、其他费用六大类。",
    "附件要求：单笔500元以上的报销必须附原始发票扫描件。1000元以上需附审批单。",
    "多人出差报销：同一出差事项可由一人代报，需附其他人员名单及分摊明细。",
    "汇率处理：境外费用按报销当日央行中间价折算人民币。",
]


# ════════════════════════════════════════════════════════════
# 七、报销单据生成（200+条）
# ════════════════════════════════════════════════════════════

# 事由模板（真实具体）
REASON_TEMPLATES = {
    "TRAVEL": [
        "赴{city}参加{event}差旅", "{city}客户拜访差旅", "赴{city}供应商考察",
        "{city}技术峰会参会", "赴{city}分公司出差", "{city}行业展会参展",
        "赴{city}合作伙伴洽谈", "{city}招标现场差旅",
    ],
    "ENTERTAIN": [
        "接待{client}来访", "{client}商务宴请", "招待{client}考察团",
        "与{client}合作签约招待", "{client}季度答谢宴",
    ],
    "OFFICE": [
        "采购部门{item}", "采购{item}", "补充{item}库存",
        "{item}季度采购", "采购{item}及{item2}",
    ],
    "TRANSPORT": [
        "月度市内交通补贴", "客户拜访出租车费", "外出办事交通费",
        "月度交通费汇总", "跨区办公交通费",
    ],
    "TELECOM": [
        "月度通讯补贴", "季度通讯费报销", "工作手机话费补贴",
    ],
    "OTHER": [
        "员工团建活动费", "部门{event}费用", "办公{item}维修费",
        "{event}场地租赁费", "快递物流费",
    ],
}

CITIES = ["上海", "北京", "深圳", "广州", "杭州", "成都", "武汉", "南京", "西安", "重庆", "苏州"]
CLIENTS = ["华为", "腾讯", "阿里巴巴", "字节跳动", "京东", "美团", "小米", "百度", "网易", "滴滴"]
ITEMS = ["办公文具", "打印耗材", "办公家具", "电脑配件", "会议室设备", "清洁用品", "茶叶咖啡"]
EVENTS = ["季度总结会", "年度团建", "技术分享会", "客户答谢会", "产品发布会", "部门培训"]


def _make_reason(etype):
    """生成真实事由"""
    templates = REASON_TEMPLATES.get(etype, REASON_TEMPLATES["OTHER"])
    tpl = random.choice(templates)
    return tpl.format(
        city=random.choice(CITIES), client=random.choice(CLIENTS),
        item=random.choice(ITEMS), item2=random.choice(ITEMS),
        event=random.choice(EVENTS),
    )


def _make_detail_items(etype, total, exp_date):
    """生成2-5条费用明细"""
    n = random.randint(2, 5)
    items = []
    remaining = total
    for i in range(n):
        if i == n - 1:
            amt = round(remaining, 2)
        else:
            amt = round(random.uniform(remaining * 0.15, remaining * 0.5), 2)
            remaining -= amt
        d = datetime.strptime(exp_date, "%Y-%m-%d")
        item_date = (d - timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d")
        items.append({
            "type": etype, "amount": amt, "date": item_date,
            "reason": _make_reason(etype),
        })
    return items


def _make_attachments(etype, amount):
    """生成附件列表"""
    pool = {
        "TRAVEL": ["行程单.pdf", "高铁票.pdf", "住宿发票.pdf", "登机牌.jpg"],
        "ENTERTAIN": ["餐饮发票.jpg", "消费明细.pdf"],
        "OFFICE": ["采购发票.pdf", "物品清单.xlsx"],
        "TRANSPORT": ["出租车票.jpg", "网约车行程.pdf"],
        "TELECOM": ["话费账单.pdf"],
        "OTHER": ["费用凭证.jpg", "说明文档.pdf"],
    }
    p = pool.get(etype, pool["OTHER"])
    n = min(random.randint(1, 3), len(p))
    return random.sample(p, n)


def _make_reject_reason():
    """生成驳回理由"""
    reasons = [
        "发票附件不全，请补充住宿水单",
        "住宿费用超出对应职级标准，请确认",
        "事由描述不清晰，请补充出差具体事项",
        "超出部门月度预算，请走特批流程",
        "餐饮发票抬头不正确，请重新开具",
        "交通费缺少起止地点说明",
        "招待费缺少招待对象信息",
        "报销金额与发票金额不一致",
        "超出报销提交时限，请说明原因",
        "附件模糊不清，请重新上传",
    ]
    return random.choice(reasons)


def _make_approval_history(expense_id, applicant_id, dept_id, amount, status, submit_dt):
    """生成完整审批历史"""
    history = []
    now = datetime.now()
    base_dt = datetime.strptime(submit_dt, "%Y-%m-%d %H:%M:%S")

    # 提交节点
    history.append({
        "node": "submit", "name": "提交申请",
        "op_id": applicant_id, "op_name": "",
        "action": "submit", "label": "提交",
        "time": submit_dt, "comment": "报销申请已提交",
    })

    # 部门经理审批
    mgr = _find_dept_manager(dept_id)
    mgr_dt = (base_dt + timedelta(hours=random.randint(2, 24))).strftime("%Y-%m-%d %H:%M:%S")
    if status in ("approved", "rejected", "paid", "archived"):
        if status == "rejected" and random.random() < 0.3:
            history.append({
                "node": "dept_manager", "name": "部门经理审批",
                "op_id": mgr["id"] if mgr else 0, "op_name": mgr["name"] if mgr else "",
                "action": "reject", "label": "驳回",
                "time": mgr_dt, "comment": _make_reject_reason(),
            })
            return history
        else:
            comments = ["同意", "同意，请注意费用标准", "同意报销", "同意，费用合理", "同意，请注意节约"]
            history.append({
                "node": "dept_manager", "name": "部门经理审批",
                "op_id": mgr["id"] if mgr else 0, "op_name": mgr["name"] if mgr else "",
                "action": "approve", "label": "通过",
                "time": mgr_dt, "comment": random.choice(comments),
            })

    # 财务审核
    fin_dt = (base_dt + timedelta(hours=random.randint(24, 48))).strftime("%Y-%m-%d %H:%M:%S")
    if status in ("approved", "paid", "archived"):
        fin_comments = ["财务审核通过", "发票已核验，审核通过", "审核通过，符合标准", "同意"]
        history.append({
            "node": "finance", "name": "财务审核",
            "op_id": 59, "op_name": "王秀英",
            "action": "approve", "label": "通过",
            "time": fin_dt, "comment": random.choice(fin_comments),
        })

    # 财务总监审批（1000+）
    if amount >= 1000 and status in ("approved", "paid", "archived"):
        fd_dt = (base_dt + timedelta(hours=random.randint(48, 72))).strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "node": "finance_director", "name": "财务总监审批",
            "op_id": 57, "op_name": "秦丽华",
            "action": "approve", "label": "通过",
            "time": fd_dt, "comment": random.choice(["同意", "同意，注意控制费用", "审批通过"]),
        })

    # 总经理审批（5000+）
    if amount >= 5000 and status in ("approved", "paid", "archived"):
        ceo_dt = (base_dt + timedelta(hours=random.randint(72, 96))).strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "node": "ceo", "name": "总经理审批",
            "op_id": 1, "op_name": "王建国",
            "action": "approve", "label": "通过",
            "time": ceo_dt, "comment": "批准",
        })

    # 打款
    if status in ("paid", "archived"):
        pay_dt = (base_dt + timedelta(days=random.randint(5, 10))).strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "node": "payment", "name": "财务打款",
            "op_id": 60, "op_name": "李桂芳",
            "action": "pay", "label": "已打款",
            "time": pay_dt, "comment": "款项已转账",
        })

    # 归档
    if status == "archived":
        arch_dt = (base_dt + timedelta(days=random.randint(35, 45))).strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "node": "archive", "name": "归档",
            "op_id": 0, "op_name": "系统",
            "action": "archive", "label": "已归档",
            "time": arch_dt, "comment": "单据已归档",
        })

    return history


def _find_dept_manager(dept_id):
    """查找部门经理"""
    for emp in EMPLOYEES:
        if emp["dept_id"] == dept_id and emp["role"] == "manager":
            return emp
    return None


def generate_expenses():
    """生成200+条报销单据"""
    now = datetime.now()
    expenses = []
    eid = 1

    # 按部门分配单据数量（销售部最多，法务最少）
    dept_weights = {
        1: 12,  # 总经办
        2: 55,  # 销售一部
        3: 42,  # 销售二部
        4: 30,  # 市场部
        5: 28,  # 技术研发部
        6: 14,  # 产品部
        7: 14,  # 运营部
        8: 12,  # 财务部
        9: 12,  # 人力资源部
        10: 10, # 行政部
        11: 6,  # 法务部
    }

    # 费用类型权重
    type_weights = [
        ("TRAVEL", 30), ("ENTERTAIN", 20), ("OFFICE", 15),
        ("TRANSPORT", 20), ("TELECOM", 8), ("OTHER", 7),
    ]
    types, tw = zip(*type_weights)

    for dept_id, count in dept_weights.items():
        dept_employees = [e for e in EMPLOYEES if e["dept_id"] == dept_id and e["role"] != "admin" and e["role"] not in ("finance", "finance_director", "ceo")]
        if not dept_employees:
            continue

        for _ in range(count):
            # 随机选择申请人
            applicant = random.choice(dept_employees)

            # 随机费用类型
            etype = random.choices(types, weights=tw, k=1)[0]

            # 金额分布（符合真实特征）
            r = random.random()
            if r < 0.40:
                amount = round(random.uniform(50, 500), 2)
            elif r < 0.70:
                amount = round(random.uniform(500, 1000), 2)
            elif r < 0.90:
                amount = round(random.uniform(1000, 5000), 2)
            else:
                amount = round(random.uniform(5000, 15000), 2)

            # 日期分布（2026年1-6月）
            month = random.randint(1, 6)
            day = random.randint(1, 28)
            exp_date = f"2026-{month:02d}-{day:02d}"

            # 状态分布
            sr = random.random()
            if sr < 0.40:
                status = "archived"
            elif sr < 0.60:
                status = "paid"
            elif sr < 0.75:
                status = "approved"
            elif sr < 0.90:
                status = "pending"
            elif sr < 0.97:
                status = "rejected"
            else:
                status = "draft"

            # 提交时间
            submit_dt = f"{exp_date} {random.randint(8,18):02d}:{random.randint(0,59):02d}:00"

            # 事由
            title = _make_reason(etype)

            # 明细
            detail = _make_detail_items(etype, amount, exp_date)

            # 附件
            attachments = _make_attachments(etype, amount)

            # 审批节点
            nodes = [{"node": "dept_manager", "name": "部门经理审批"}, {"node": "finance", "name": "财务审核"}]
            if amount >= 1000:
                nodes.append({"node": "finance_director", "name": "财务总监审批"})
            if amount >= 5000:
                nodes.append({"node": "ceo", "name": "总经理审批"})

            # 审批历史
            history = _make_approval_history(eid, applicant["id"], dept_id, amount, status, submit_dt)
            # 填充操作人姓名
            for h in history:
                if not h["op_name"]:
                    emp = next((e for e in EMPLOYEES if e["id"] == h["op_id"]), None)
                    h["op_name"] = emp["name"] if emp else "未知"

            # 当前节点
            cur_node = "submit"
            if status == "pending":
                for n in nodes:
                    if not any(h["node"] == n["node"] for h in history):
                        cur_node = n["node"]
                        break

            expenses.append({
                "id": eid, "title": title, "applicant_id": applicant["id"],
                "dept_id": dept_id, "amount": amount, "status": status,
                "current_node": cur_node, "exp_date": exp_date,
                "submit_time": submit_dt if status != "draft" else None,
                "detail": detail, "attachments": attachments,
                "nodes": nodes, "history": history,
                "created": submit_dt if status != "draft" else f"{exp_date} 10:00:00",
            })
            eid += 1

    # ── 后处理：将部分 pending 单据推进到更高审批节点 ──
    # 确保财务总监、总经理有待审批单据
    pending_list = [e for e in expenses if e["status"] == "pending"]
    random.shuffle(pending_list)

    # 推进 8 条到 finance_director 节点（金额 1000-5000）
    fd_count = 0
    for e in pending_list:
        if fd_count >= 8:
            break
        if e["amount"] >= 1000 and e["current_node"] == "dept_manager":
            e["current_node"] = "finance_director"
            # 添加部门经理+财务已审批的历史
            mgr = _find_dept_manager(e["dept_id"])
            base_dt = datetime.strptime(e["submit_time"], "%Y-%m-%d %H:%M:%S")
            e["history"] = [
                {"node": "submit", "name": "提交申请", "op_id": e["applicant_id"], "op_name": "",
                 "action": "submit", "label": "提交", "time": e["submit_time"], "comment": "报销申请已提交"},
                {"node": "dept_manager", "name": "部门经理审批", "op_id": mgr["id"] if mgr else 0,
                 "op_name": mgr["name"] if mgr else "", "action": "approve", "label": "通过",
                 "time": (base_dt + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), "comment": "同意"},
                {"node": "finance", "name": "财务审核", "op_id": 59, "op_name": "王秀英",
                 "action": "approve", "label": "通过",
                 "time": (base_dt + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"), "comment": "财务审核通过"},
            ]
            fd_count += 1

    # 推进 4 条到 ceo 节点（金额 5000+）
    ceo_count = 0
    for e in pending_list:
        if ceo_count >= 4:
            break
        if e["amount"] >= 5000 and e["current_node"] == "dept_manager":
            e["current_node"] = "ceo"
            mgr = _find_dept_manager(e["dept_id"])
            base_dt = datetime.strptime(e["submit_time"], "%Y-%m-%d %H:%M:%S")
            e["history"] = [
                {"node": "submit", "name": "提交申请", "op_id": e["applicant_id"], "op_name": "",
                 "action": "submit", "label": "提交", "time": e["submit_time"], "comment": "报销申请已提交"},
                {"node": "dept_manager", "name": "部门经理审批", "op_id": mgr["id"] if mgr else 0,
                 "op_name": mgr["name"] if mgr else "", "action": "approve", "label": "通过",
                 "time": (base_dt + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), "comment": "同意"},
                {"node": "finance", "name": "财务审核", "op_id": 59, "op_name": "王秀英",
                 "action": "approve", "label": "通过",
                 "time": (base_dt + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"), "comment": "财务审核通过"},
                {"node": "finance_director", "name": "财务总监审批", "op_id": 57, "op_name": "秦丽华",
                 "action": "approve", "label": "通过",
                 "time": (base_dt + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S"), "comment": "同意"},
            ]
            ceo_count += 1

    # 推进 5 条到 finance 节点（金额不限）
    fin_count = 0
    for e in pending_list:
        if fin_count >= 5:
            break
        if e["current_node"] == "dept_manager" and e["amount"] < 1000:
            e["current_node"] = "finance"
            mgr = _find_dept_manager(e["dept_id"])
            base_dt = datetime.strptime(e["submit_time"], "%Y-%m-%d %H:%M:%S")
            e["history"] = [
                {"node": "submit", "name": "提交申请", "op_id": e["applicant_id"], "op_name": "",
                 "action": "submit", "label": "提交", "time": e["submit_time"], "comment": "报销申请已提交"},
                {"node": "dept_manager", "name": "部门经理审批", "op_id": mgr["id"] if mgr else 0,
                 "op_name": mgr["name"] if mgr else "", "action": "approve", "label": "通过",
                 "time": (base_dt + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"), "comment": "同意"},
            ]
            fin_count += 1

    # 填充操作人姓名
    for e in expenses:
        for h in e["history"]:
            if not h["op_name"]:
                emp = next((em for em in EMPLOYEES if em["id"] == h["op_id"]), None)
                h["op_name"] = emp["name"] if emp else "未知"

    return expenses


# ════════════════════════════════════════════════════════════
# 八、预算初始化（与报销单总额一致）
# ════════════════════════════════════════════════════════════
def init_budgets(expenses):
    """根据实际报销单计算预算使用额"""
    budgets = {}
    for dept in DEPARTMENTS:
        base = dept["budget"]
        for year in (2025, 2026):
            total = int(base * (0.9 if year == 2025 else 1.0))
            used = round(sum(
                e["amount"] for e in expenses
                if e["dept_id"] == dept["id"]
                and e["status"] in ("approved", "paid", "archived")
                and int(e["exp_date"][:4]) == year
            ), 2)
            budgets[(dept["id"], year)] = {"dept_id": dept["id"], "year": year, "total": total, "used": used}
    return budgets


# ════════════════════════════════════════════════════════════
# 九、初始化入口
# ════════════════════════════════════════════════════════════
EMPLOYEES = build_employees()
EXPENSES = generate_expenses()
BUDGETS = init_budgets(EXPENSES)
NEXT_ID = len(EXPENSES) + 1

# 设置部门经理引用
for dept in DEPARTMENTS:
    mgr = next((e for e in EMPLOYEES if e["dept_id"] == dept["id"] and e["role"] == "manager"), None)
    dept["mgr"] = mgr["id"] if mgr else 0
