# 企业级 OA 报销系统 —— Agent 智能化改造

> CS599 人工智能与大模型应用 · 方向二：企业级应用软件的 Agent 改造

## 项目简介

本项目是一套完整的企业级 OA 报销管理系统，基于 **Python Flask + 内存数据** 构建传统人工报销全流程，并通过 **LangChain + LangGraph + DeepSeek API** 进行 Agentic AI 智能化改造。

原始系统完整保留所有人工审批功能，AI 功能以增量模块形式接入，支持双模式切换对比。

### 核心改造能力

| 模块 | 功能 | 技术实现 |
|------|------|---------|
| 智能填报助手 | 自然语言转表单、实时合规提示 | 关键词解析 + 规则校验 |
| 多级审批引擎 | 自动校验 + 风险评分 + 决策建议 | LangGraph 三通道状态机 |
| 合规审计 | 全量扫描、异常检测、风险分级 | 规则引擎 + 历史分析 |
| 制度问答 | RAG 检索 + LLM 推理 + 引用溯源 | Chroma + Agentic RAG |
| 数据分析 | 自然语言查询 + 自动图表 | LLM 解析 + ECharts |
| 多智能体协调 | Supervisor 统一调度 + 结果汇总 | Supervisor Agent |

## 技术栈

| 分类 | 选型 |
|------|------|
| LLM | DeepSeek API（主）+ MiMo API（备） |
| Agent 框架 | LangChain + LangGraph |
| 协议 | MCP（Model Context Protocol） |
| 知识库 | Chroma 向量数据库 + Agentic RAG |
| 可观测性 | LangSmith + 结构化日志 |
| 后端 | Flask（原始系统）+ FastAPI（Agent 服务） |
| 前端 | HTML + Tailwind CSS + ECharts |
| 部署 | Docker + Docker Compose |

## 快速开始

### 环境要求

- Python 3.11+
- pip

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/jck7/cs599-project.git
cd cs599-project

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 4. 启动 OA 系统
cd src/legacy_system
python app.py

# 5. 访问
# 浏览器打开 http://127.0.0.1:5000
```

### Docker 部署

```bash
OA系统已部署到云服务器上

# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 2. 构建并启动
docker-compose up -d --build

# 3. 访问
OA 系统：http://8.130.41.88:5000
```

## 测试账号

登录页提供快速登录，点击角色卡片即可选择账号：

| 角色 | 姓名 | 工号 | 权限 |
|------|------|------|------|
| 普通员工 | 张伟 | EMP0001 | 发起报销、查看自己的单据 |
| 部门经理 | 王强 | EMP0003 | 审批本部门报销 |
| 财务人员 | 刘会计 | EMP0053 | 财务审核 + 打款 |
| 财务总监 | 李总 | EMP0064 | 审批 1000 元以上 |
| 总经理 | 王总 | EMP0001 | 审批 5000 元以上 |
| 管理员 | 管理员 | ADMIN01 | 全部管理权限 |

## 目录结构

```
cs599-project/
├── .env.example                    # 环境变量模板
├── requirements.txt                # Python 依赖
├── Dockerfile                      # Docker 镜像配置
├── docker-compose.yml              # 双服务编排
├── docs/
│   ├── architecture.md             # 项目架构文档
│   ├── deploy-guide.md             # 腾讯云部署指南
│   └── CS599_Report_v4.docx        # 课程报告
│
├── src/
│   ├── agent/                      # 智能中台核心模块
│   │   ├── config.py               # 配置管理
│   │   ├── service.py              # Agent 统一服务
│   │   ├── api.py                  # FastAPI 服务入口
│   │   ├── graph/
│   │   │   ├── state.py            # 全局状态定义
│   │   │   └── workflow.py         # 三通道审批工作流
│   │   ├── agents/
│   │   │   ├── info_checker.py     # 信息校验 Agent
│   │   │   ├── budget_checker.py   # 预算校验 Agent
│   │   │   ├── risk_analyzer.py    # 风险识别 Agent
│   │   │   ├── decision_maker.py   # 审批决策 Agent
│   │   │   ├── fill_assistant.py   # 填报助手 Agent
│   │   │   ├── audit_agent.py      # 合规审计 Agent
│   │   │   └── qa_agent.py         # 知识问答 Agent
│   │   ├── tools/
│   │   │   ├── mcp_server.py       # MCP 协议服务端
│   │   │   ├── employee_tools.py   # 员工信息工具
│   │   │   ├── budget_tools.py     # 预算查询工具
│   │   │   ├── history_tools.py    # 历史记录工具
│   │   │   ├── rule_tools.py       # 审批规则工具
│   │   │   ├── reimbursement_tools.py  # 报销操作工具
│   │   │   └── report_tools.py     # 报表分析工具
│   │   ├── knowledge/
│   │   │   ├── vector_store.py     # Chroma 向量库
│   │   │   ├── policy_kb.py        # 财务制度知识库
│   │   │   └── user_memory.py      # 用户行为记忆
│   │   ├── llm/
│   │   │   ├── llm_client.py       # 统一 LLM 客户端
│   │   │   └── fallback_service.py # 离线知识库兜底
│   │   └── orchestrator/
│   │       └── supervisor_agent.py # Supervisor 协调者
│   │
│   └── legacy_system/              # 原始系统
│       ├── app.py                  # Flask 路由 + API
│       ├── mock_data.py            # 模拟数据生成
│       ├── templates/              # 15 个 HTML 页面
│       └── static/                 # CSS + JS
```

## 核心业务规则

### 四级审批流

- **0-1000 元**：员工 → 部门经理 → 财务 → 完成
- **1000-5000 元**：员工 → 部门经理 → 财务 → 财务总监 → 完成
- **5000 元以上**：员工 → 部门经理 → 财务 → 财务总监 → 总经理 → 完成

### 三通道分级审批（AI 优化）

| 通道 | 触发条件 | LLM 调用次数 | 预期耗时 |
|------|---------|-------------|---------|
| 极速通道 | < 1000 元且无历史违规 | 1 次 | < 500ms |
| 标准通道 | 1000-5000 元 | 2 次 | 10-15s |
| 严格通道 | > 5000 元或高风险 | 2-4 次 | 15-30s |

### 内置数据

- 11 个部门、75 名员工
- 211+ 条报销单据（覆盖全部 6 种状态）
- 30 条财务制度文档
- 完整的部门年度预算数据

## 详细文档

- [项目架构文档](docs/architecture.md)
- [课程报告](docs/CS599_Report_v4.docx)

## License

本项目为 CS599 课程大作业，仅供学术用途。


## 项目状态
- [x] Proposal
- [x] MVP
- [x] Final
