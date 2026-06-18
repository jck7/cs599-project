# OA报销系统智能审批Agent改造 



## 项目简介

基于传统企业OA报销系统，引入Agentic AI技术实现报销单据智能审核、自动路由与风险识别，将人工审核效率提升80%以上。



 ## 方向

方向二：企业级应用软件的 Agent 改造 



## 技术栈

- AI IDE: Trae CN 

- LLM: DeepSeek API 

- Agent框架: LangGraph + LangChain

- 协议: Function Calling 

- 容器: Docker  

- 数据存储: SQLite  

- 可观测性: LangSmith



## 目录结构

src/

├── agents/          # 各审批 Agent 逻辑

├── graph/           # LangGraph 工作流编排

├── tools/           # 工具函数与业务 API 封装

├── database/        # 模拟 OA 数据库与数据模型

├── api/             # 对外服务接口

└── config.py        # 配置管理



## 环境搭建
1. 安装依赖：`pip install -r requirements.txt`
2. 复制环境变量：`cp .env.example .env`，在 `.env` 中填入 DeepSeek API Key
3. 初始化模拟数据库：`python src/database/init_db.py`
4. 启动服务：`python src/api/app.py`

## 项目状态
- [x] Proposal
- [ ] MVP
- [ ] Final