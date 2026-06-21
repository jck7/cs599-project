# 企业级 OA 报销系统 —— 项目架构文档

## 1. 项目总览

本项目是一套完整的企业级 OA 报销管理系统，包含两个核心模块：

| 模块 | 目录 | 技术栈 | 职责 |
|------|------|--------|------|
| 原始系统 | `src/legacy_system/` | Flask + Jinja2 + 内存数据 | 传统人工报销全流程 |
| 智能中台 | `src/agent/` | LangChain + LangGraph + DeepSeek/MiMo API | AI 辅助审批、问答、审计、分析 |

两个模块通过标准 API 接口对接，可独立运行，互不影响。

---

## 2. 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         浏览器（前端）                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ 原始页面  │ │ 智能看板  │ │ 智能问答  │ │ 智能审计  │ │ 数据分析  │ │
│  │ 9个页面   │ │ AI看板   │ │ QA页面   │ │ 审计页面  │ │ 分析页面  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│        HTML + CSS(本地) + ECharts(CDN) + 原生 JS                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────────┐
│                    Flask 路由层（app.py）                            │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐    │
│  │  原始业务路由（~20个）      │  │  AI 增量路由（~10个 /api/ai/*）│    │
│  │  /dashboard /apply /...  │  │  /api/ai/analyze /qa /audit  │    │
│  └──────────────────────────┘  └──────────────┬───────────────┘    │
├────────────────────────────────────────────────┼────────────────────┤
│                                               │                    │
│  ┌────────────────────────────────────────────▼────────────────┐   │
│  │              Agent 智能中台（service.py）                    │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │           Supervisor 协调者 Agent                      │  │   │
│  │  │     统一接收任务 → 分发 → 汇总结果                     │  │   │
│  │  └────┬──────────┬──────────┬──────────┬────────────────┘  │   │
│  │       │          │          │          │                    │   │
│  │  ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌────────┐  │   │
│  │  │填报助手│ │审批引擎│ │ 审计   │ │ 问答   │ │数据分析│  │   │
│  │  │fill_   │ │info_   │ │audit_  │ │ qa_    │ │report_ │  │   │
│  │  │assistant│ │checker │ │agent   │ │ agent  │ │tools   │  │   │
│  │  │        │ │budget_ │ │        │ │        │ │        │  │   │
│  │  │        │ │checker │ │        │ │        │ │        │  │   │
│  │  │        │ │risk_   │ │        │ │        │ │        │  │   │
│  │  │        │ │analyzer│ │        │ │        │ │        │  │   │
│  │  │        │ │decision│ │        │ │        │ │        │  │   │
│  │  │        │ │_maker  │ │        │ │        │ │        │  │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  工具层（MCP 协议封装）                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │   │
│  │  │employee_  │ │budget_   │ │history_  │ │rule_     │     │   │
│  │  │tools      │ │tools     │ │tools     │ │tools     │     │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │   │
│  │  ┌──────────────────┐ ┌──────────────────┐                │   │
│  │  │reimbursement_    │ │report_tools      │                │   │
│  │  │tools             │ │                  │                │   │
│  │  └──────────────────┘ └──────────────────┘                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  知识与记忆层                                                │   │
│  │  ┌──────────────────┐  ┌──────────────────┐               │   │
│  │  │ Chroma 向量知识库  │  │ 用户行为长期记忆  │               │   │
│  │  │ 30+ 财务制度文档  │  │ 报销行为画像      │               │   │
│  │  └──────────────────┘  └──────────────────┘               │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  LLM 调用层                                                │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │  统一 LLM 客户端（单例 + 场景参数 + 重试 + 降级）     │   │   │
│  │  │  DeepSeek API ←→ MiMo API ←→ 规则引擎 ←→ 离线知识库 │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────────────┤
│               原始系统数据层（mock_data.py）                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ 11部门   │ │ 75员工   │ │ 211+报销单│ │ 预算数据  │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. 目录结构详解

```
cs599-project/
├── .env.example                    # 环境变量模板
├── .env                            # 实际环境变量（不入库）
├── requirements.txt                # Python 依赖
├── docs/
│   ├── architecture.md             # 本文件
│   └── CS599_Report_v4.docx        # 课程报告
│
├── src/
│   ├── __init__.py
│   │
│   ├── agent/                      # ━━━ 智能中台核心模块 ━━━
│   │   ├── __init__.py
│   │   ├── config.py               # 配置管理（环境变量读取）
│   │   ├── service.py              # Agent 统一服务封装
│   │   ├── api.py                  # FastAPI 独立服务入口
│   │   ├── llm_client.py           # LLM 客户端兼容层（转发）
│   │   │
│   │   ├── graph/                  # LangGraph 状态机
│   │   │   ├── state.py            # 全局状态定义（TypedDict）
│   │   │   └── workflow.py         # 三通道审批工作流
│   │   │
│   │   ├── agents/                 # 7 个专业 Agent
│   │   │   ├── info_checker.py     # 信息完整性校验（纯规则）
│   │   │   ├── budget_checker.py   # 预算与费用标准校验（纯规则）
│   │   │   ├── risk_analyzer.py    # 风险识别（规则+LLM）
│   │   │   ├── decision_maker.py   # 审批决策（规则+LLM）
│   │   │   ├── fill_assistant.py   # 填报助手（自然语言解析）
│   │   │   ├── audit_agent.py      # 合规审计（全量扫描）
│   │   │   └── qa_agent.py         # 知识库问答（RAG+LLM）
│   │   │
│   │   ├── tools/                  # MCP 协议工具集
│   │   │   ├── base.py             # 工具基类（桥接原始数据）
│   │   │   ├── mcp_server.py       # MCP 服务端
│   │   │   ├── employee_tools.py   # 员工信息查询
│   │   │   ├── budget_tools.py     # 预算查询与校验
│   │   │   ├── history_tools.py    # 历史记录与异常检测
│   │   │   ├── rule_tools.py       # 审批规则与费用标准
│   │   │   ├── reimbursement_tools.py  # 报销单操作
│   │   │   └── report_tools.py     # 报表分析
│   │   │
│   │   ├── knowledge/              # 知识库与记忆
│   │   │   ├── vector_store.py     # Chroma 向量库封装
│   │   │   ├── policy_kb.py        # 财务制度知识库（30+文档）
│   │   │   └── user_memory.py      # 用户行为长期记忆
│   │   │
│   │   ├── llm/                    # LLM 调用层
│   │   │   ├── llm_client.py       # 统一客户端（单例+重试+降级）
│   │   │   └── fallback_service.py # 离线知识库兜底
│   │   │
│   │   ├── orchestrator/           # 多智能体协调
│   │   │   └── supervisor_agent.py # Supervisor 协调者
│   │   │
│   │   ├── memory/                 # 行为画像
│   │   │   └── user_behavior.py    # 员工报销行为画像
│   │   │
│   │   ├── test_cases.py           # 测试用例
│   │   └── test_mimo.py            # MiMo API 测试
│   │
│   └── legacy_system/              # ━━━ 原始系统 ━━━
│       ├── app.py                  # Flask 路由 + API（~1200行）
│       ├── mock_data.py            # 模拟数据生成（~600行）
│       │
│       ├── templates/              # 15 个 HTML 页面
│       │   ├── layout.html         # 全局布局（侧边栏+顶栏）
│       │   ├── login.html          # 登录页
│       │   ├── dashboard.html      # 数据看板（ECharts）
│       │   ├── apply.html          # 发起报销（分步表单）
│       │   ├── my_reimburse.html   # 我的报销列表
│       │   ├── approval.html       # 审批中心
│       │   ├── detail.html         # 报销详情+审批时间轴
│       │   ├── budget.html         # 预算管理
│       │   ├── rule.html           # 费用标准
│       │   ├── employee.html       # 员工管理
│       │   ├── ai_dashboard.html   # AI 智能看板
│       │   ├── ai_audit.html       # 智能审计中心
│       │   ├── ai_qa.html          # 智能问答
│       │   ├── ai_analysis.html    # 智能数据分析
│       │   └── ai_comparison.html  # 改造前后对比
│       │
│       └── static/
│           ├── css/style.css       # 全局样式（Ant Design Pro 规范）
│           └── js/
│               ├── common.js       # 公共交互（Modal/Toast/Tab）
│               └── ai_module.js    # AI 前端交互模块
```

---

## 4. 核心数据流

### 4.1 报销审批流程

```
员工填写 → [AI填报助手] → 提交
                              │
                    ┌─────────▼──────────┐
                    │   金额 & 风险路由    │
                    └──┬──────┬──────────┘
                       │      │      │
              ┌────────▼┐ ┌──▼────┐ ┌▼────────┐
              │极速通道  │ │标准通道│ │严格通道  │
              │<1000元  │ │1000-  │ │>5000元  │
              │1次LLM   │ │5000元 │ │完整链路  │
              └────┬────┘ └──┬────┘ └──┬──────┘
                   │         │         │
              ┌────▼─────────▼─────────▼──────┐
              │         审批结论输出            │
              │  自动通过 / 驳回 / 转人工       │
              └───────────────────────────────┘
```

### 4.2 智能问答流程

```
用户提问
    │
    ▼
意图判断（关键词匹配）
    │
    ├── 财务制度类 ──→ RAG 检索知识库 ──→ 注入上下文 ──→ LLM 生成回答
    │                                                    │
    └── 通用问题 ────→ 直接 LLM 推理 ──────────────────→ 返回回答
                                                        │
                                                  ┌─────▼─────┐
                                                  │ API 故障？  │
                                                  └──┬─────┬──┘
                                               是 │     │ 否
                                           ┌──────▼──┐  │
                                           │离线知识库│  │
                                           │  兜底    │  │
                                           └─────────┘  │
                                                        ▼
                                                    最终回答
```

### 4.3 LLM 降级机制

```
LLM 调用请求
    │
    ▼
检查缓存（单例模式）
    │
    ├── 缓存命中 ──→ 直接调用 ──→ 成功 ──→ 返回结果
    │                    │
    │                    └── 失败 ──→ 判断可重试？
    │                                    │
    │                              ┌─────▼─────┐
    │                              │ 可重试？    │
    │                              └──┬─────┬──┘
    │                            是 │     │ 否
    │                        ┌──────▼─┐   │
    │                        │重试2次  │   │
    │                        └────┬───┘   │
    │                             │       │
    │                        ┌────▼───────▼──┐
    │                        │  全部失败      │
    │                        └───────┬───────┘
    │                                │
    │                        ┌───────▼───────┐
    │                        │  触发降级      │
    │                        └───┬───────┬───┘
    │                     问答场景│       │审批场景
    │                    ┌───────▼──┐ ┌──▼────────┐
    │                    │离线知识库 │ │规则引擎兜底│
    │                    └──────────┘ └───────────┘
    │
    └── 缓存未命中 ──→ 初始化 LLM ──→ 存入缓存 ──→ 调用
```

---

## 5. Agent 职责矩阵

| Agent | 文件 | 输入 | 输出 | 调用 LLM | 触发场景 |
|-------|------|------|------|----------|---------|
| 信息校验 | `info_checker.py` | 报销单数据 | 校验结果+缺失项 | 否 | 每次审批 |
| 预算校验 | `budget_checker.py` | 报销单+申请人 | 预算状态+超标项 | 否 | 每次审批 |
| 风险识别 | `risk_analyzer.py` | 报销单+历史记录 | 风险评分 0-100 | 仅高风险 | 标准/严格通道 |
| 审批决策 | `decision_maker.py` | 前三步结果 | 通过/驳回/转人工 | 是 | 每次审批 |
| 填报助手 | `fill_assistant.py` | 用户输入文本 | 解析结果+提示 | 否 | 发起报销 |
| 审计 Agent | `audit_agent.py` | 全量报销单 | 风险发现列表 | 否 | 审计页面 |
| 问答 Agent | `qa_agent.py` | 用户问题 | 回答+来源 | 是 | 问答页面 |

---

## 6. 工具层接口清单

### 6.1 员工工具（employee_tools.py）

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `get_employee_info` | employee_id | 姓名/工号/部门/职级/角色 | 员工基本信息 |
| `get_employee_expense_limits` | employee_id | 差旅/餐饮/交通上限 | 职级对应报销标准 |
| `get_department_manager` | department_id | 经理ID/姓名 | 部门经理查询 |

### 6.2 预算工具（budget_tools.py）

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `get_department_budget` | department_id, year | 总额/已用/剩余/使用率 | 部门预算查询 |
| `check_budget_affordable` | department_id, amount | 是否可承担/差额 | 预算校验 |

### 6.3 历史工具（history_tools.py）

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `get_employee_expense_history` | employee_id, days | 笔数/总额/状态分布 | 历史报销记录 |
| `detect_frequency_anomaly` | employee_id, days, threshold | 是否异常/频率 | 高频报销检测 |
| `detect_amount_spike` | employee_id, days | 是否飙升/比值 | 金额异常检测 |

### 6.4 规则工具（rule_tools.py）

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `get_approval_rule` | amount | 节点列表/节点数 | 审批流规则 |
| `check_expense_standard` | level, type, amount | 是否超标/差额 | 费用标准校验 |
| `get_expense_type_info` | - | 费用类型列表 | 类型查询 |

### 6.5 报销工具（reimbursement_tools.py）

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `parse_natural_language_expense` | text | 标题/明细/总额 | 自然语言解析 |
| `get_expense_summary` | employee_id, year | 笔数/总额/分布 | 年度汇总 |
| `auto_fill_suggestions` | employee_id | 常用事由/类型 | 智能补全 |

### 6.6 报表工具（report_tools.py）

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `query_expense_stats` | query_type, year, month | 排名/趋势/分布 | 统计查询 |
| `detect_expense_anomalies` | days | 异常列表 | 异常检测 |
| `generate_monthly_report` | year, month | 月度简报 | 报告生成 |

---

## 7. 知识库架构

### 7.1 向量知识库（vector_store.py）

```
ChromaVectorStore（优先）
    │
    ├── 持久化存储：data/chroma_db/
    ├── 语义检索：cosine 相似度
    └── 自动降级：Chroma 不可用时 → SimpleVectorStore
                                              │
                                    ┌─────────▼──────────┐
                                    │ SimpleVectorStore   │
                                    │ 字符重叠匹配         │
                                    │ 无外部依赖           │
                                    └────────────────────┘
```

### 7.2 财务制度知识库（policy_kb.py）

内置 30+ 条制度文档，覆盖六大类：

| 类别 | 示例内容 |
|------|---------|
| 报销流程 | 审批流程、提交时限、驳回处理 |
| 发票要求 | 抬头税号、真伪校验、粘贴规范 |
| 差旅标准 | 住宿上限、交通选择、餐饮补助 |
| 预算规则 | 编制流程、使用监控、追加申请 |
| 审批权限 | 金额分级、会签规则 |
| 特殊事项 | 培训费、团建费、预借差旅 |

---

## 8. 前端页面清单

### 8.1 原始系统页面（9个）

| 页面 | 文件 | 功能 |
|------|------|------|
| 登录 | `login.html` | 多角色快速登录 |
| 工作台 | `dashboard.html` | 指标卡片+ECharts图表+待办 |
| 发起报销 | `apply.html` | 分步表单+费用明细+附件 |
| 我的报销 | `my_reimburse.html` | 列表+筛选+撤回+重提 |
| 审批中心 | `approval.html` | 待审/已审+通过/驳回/批量 |
| 报销详情 | `detail.html` | 基本信息+明细+时间轴 |
| 预算管理 | `budget.html` | 部门预算+使用率+趋势图 |
| 费用标准 | `rule.html` | 职级标准+审批流说明 |
| 员工管理 | `employee.html` | 员工列表+搜索筛选 |

### 8.2 AI 增强页面（5个）

| 页面 | 文件 | 功能 |
|------|------|------|
| 智能看板 | `ai_dashboard.html` | AI处理率+风险拦截+趋势图 |
| 智能审计 | `ai_audit.html` | 风险扫描+审计工单+图表 |
| 智能问答 | `ai_qa.html` | 对话式问答+SSE流式输出 |
| 数据分析 | `ai_analysis.html` | 自然语言查询+自动图表 |
| 效果对比 | `ai_comparison.html` | 改造前后量化对比 |

---

## 9. 配置管理

所有配置通过 `.env` 文件管理，使用 `python-dotenv` 加载：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `USE_REAL_LLM` | false | 是否启用真实 LLM |
| `LLM_PROVIDER` | deepseek | 模型提供方 |
| `DEEPSEEK_API_KEY` | - | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | https://api.deepseek.com | API 地址 |
| `DEEPSEEK_MODEL` | deepseek-chat | 模型名称 |
| `MIMO_API_KEY` | - | MiMo API Key |
| `MIMO_BASE_URL` | https://api.xiaomimimo.com/v1 | API 地址 |
| `MIMO_MODEL_NAME` | mimo-v2.5-pro | 模型名称 |
| `LLM_MAX_RETRIES` | 2 | 重试次数 |
| `LLM_RETRY_DELAY` | 1.0 | 重试间隔(秒) |
| `LLM_FALLBACK_ENABLED` | true | 是否启用降级 |
| `RISK_LOW_THRESHOLD` | 30 | 低风险阈值 |
| `RISK_MEDIUM_THRESHOLD` | 60 | 中风险阈值 |
| `RISK_HIGH_THRESHOLD` | 80 | 高风险阈值 |
| `AUTO_APPROVE_AMOUNT` | 1000 | 自动通过金额上限 |
| `MANUAL_REVIEW_AMOUNT` | 5000 | 转人工金额上限 |

---

## 10. 数据模型

### 10.1 报销单结构

```python
{
    "id": int,                    # 报销单ID
    "title": str,                 # 标题
    "applicant_id": int,          # 申请人ID
    "dept_id": int,               # 部门ID
    "amount": float,              # 总金额
    "status": str,                # draft/pending/approved/rejected/paid/archived
    "current_node": str,          # 当前审批节点
    "exp_date": str,              # 费用日期
    "submit_time": str,           # 提交时间
    "detail": [                   # 费用明细
        {"type": str, "amount": float, "date": str, "reason": str}
    ],
    "attachments": [str],         # 附件列表
    "nodes": [                    # 审批节点
        {"node": str, "name": str}
    ],
    "history": [                  # 审批历史
        {"node": str, "name": str, "op_id": int, "op_name": str,
         "action": str, "label": str, "time": str, "comment": str}
    ],
    "created": str,               # 创建时间
}
```

### 10.2 部门结构

```python
{"id": int, "name": str, "code": str, "budget": int, "mgr": int}
```

### 10.3 员工结构

```python
{
    "id": int, "name": str, "emp_no": str, "dept_id": int,
    "level": str, "role": str, "join_date": str, "phone": str, "email": str
}
```

---

## 11. API 接口清单

### 11.1 原始业务 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/approve` | 审批通过/驳回 |
| POST | `/api/withdraw` | 撤回报销单 |
| POST | `/api/pay` | 财务打款 |
| POST | `/api/batch_approve` | 批量审批 |
| POST | `/api/resubmit` | 重新提交 |
| GET | `/api/expense/<id>` | 获取报销单JSON |

### 11.2 AI 增量 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai/status` | AI 服务状态 |
| GET | `/api/ai/analyze/<id>` | 报销单AI分析 |
| POST | `/api/ai/fill_assist` | 填报助手 |
| POST | `/api/ai/qa` | 知识问答（同步） |
| POST | `/api/ai/qa/stream` | 知识问答（SSE流式） |
| POST | `/api/ai/audit` | 合规审计扫描 |
| POST | `/api/ai/analysis` | 数据分析 |

---

## 12. 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动原始系统（Flask，端口 5000）
cd src/legacy_system && python app.py

# 启动 Agent 服务（FastAPI，端口 8000，可选）
cd ../.. && python -m agent.api
```
