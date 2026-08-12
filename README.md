# 团队知识库助手

面向团队的 RAG 知识库问答平台。支持创建知识空间、上传文档、管理成员权限，并通过自然语言与知识库内容进行对话。

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI + Uvicorn |
| **数据库** | MySQL 8 (aiomysql + SQLAlchemy 异步 ORM) |
| **向量数据库** | ChromaDB |
| **LLM** | 通义千问 Qwen3.7-Plus (阿里云 DashScope) |
| **RAG 框架** | LangChain (LCEL)、LangGraph |
| **Embedding** | sentence-transformers |
| **文档解析** | PyPDF、docx2txt |
| **前端** | React 18 + Vite 6 + TypeScript 5.8 |
| **样式** | Tailwind CSS 3 |
| **状态管理** | Zustand 5 |
| **路由** | React Router 7 |

## 功能

- **用户系统** — 注册、登录、个人资料编辑
- **知识库管理** — 创建/编辑/删除知识库（支持私有和公开）
- **文档管理** — 上传、解析、列表、下载、删除（支持 .txt / .pdf / .docx）
- **RAG 问答** — 文档自动切片 → Embedding → 向量检索 → LLM 生成回答（流式 SSE 输出）
  - 多查询检索（查询改写扩展覆盖范围）
  - CrossEncoder 重排序提升结果精度
  - 引用来源展示（可查看原文片段和匹配分数）
- **会话管理** — 多会话支持、历史记录、会话重命名、删除
- **成员权限** — 支持 owner / admin / viewer 三种角色

## 快速开始

### 前置要求

- Python 3.13+
- Node.js 18+
- MySQL 8 (数据库需提前创建，如 `rag`)
- 阿里云 DashScope API Key

### 1. 克隆项目并配置后端

```bash
cd backend
cp .env .env.local   # 编辑 .env.local 填入 API Key
```

`.env` 文件内容：

```env
OPENAI_API_KEY=your_dashscope_api_key
```

数据库连接默认使用 `mysql+aiomysql://root:123456@localhost/rag?charset=utf8mb4`，可通过环境变量 `DATABASE_URL` 覆盖。

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python database_init.py    # 初始化数据库表
uvicorn main:app --reload --port 8000
```

API 文档地址：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认运行在 http://localhost:5173

## 项目结构

```
RAG-project/
├── backend/
│   ├── config/          # 数据库配置
│   ├── crud/            # 数据访问层（纯数据库操作）
│   ├── interfaces/      # API 路由层（FastAPI 路由）
│   ├── model/           # SQLAlchemy ORM 模型
│   ├── schemas/         # Pydantic 请求/响应模型
│   ├── services/        # 业务逻辑层（流程编排）
│   ├── main.py          # 应用入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/         # 后端 API 调用封装
│   │   ├── components/  # 通用组件
│   │   ├── pages/       # 页面组件
│   │   └── store/       # 全局状态
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## API 概览

### 用户认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login` | 登录 |
| POST | `/register` | 注册 |
| PUT | `/update` | 更新个人信息 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge/bases/list` | 知识库列表 |
| GET | `/knowledge/bases/{id}` | 知识库详情 |
| POST | `/knowledge/bases/create` | 创建知识库 |
| PUT | `/knowledge/bases/update/{id}` | 更新知识库 |
| DELETE | `/knowledge/bases/delete/{id}` | 删除知识库 |

### 成员

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge/bases/knowledge-bases/{kbId}/members` | 成员列表 |
| POST | `/knowledge/bases/knowledge-bases/{kbId}/members` | 添加成员 |
| PUT | `/knowledge/bases/knowledge-bases/{kbId}/members/{memberId}` | 修改角色 |
| DELETE | `/knowledge/bases/knowledge-bases/{kbId}/members/{memberId}` | 移除成员 |

### 文档

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/documents/knowledge-bases/{kbId}/documents` | 文档列表 |
| POST | `/documents/knowledge-bases/{kbId}/add` | 上传文档 |
| DELETE | `/documents/remove/{id}` | 删除文档 |
| GET | `/documents/{id}/download` | 下载文档 |

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/knowledge-bases/{kbId}/chat` | 非流式对话 |
| POST | `/knowledge-bases/{kbId}/chat/stream` | 流式对话（SSE） |
| GET | `/knowledge-bases/{kbId}/sessions` | 会话列表 |
| GET | `/knowledge-bases/{kbId}/sessions/{sessionId}/messages` | 会话消息 |
| DELETE | `/knowledge-bases/{kbId}/sessions/{sessionId}` | 删除会话 |
| PUT | `/knowledge-bases/{kbId}/sessions/{sessionId}/title` | 重命名会话 |

## 架构说明

### 三层架构

```
interfaces/ (路由层) → services/ (业务层) → crud/ (数据层)
```

- **interfaces** — 接收请求、参数校验、调用 service、返回响应
- **services** — 编排业务流程（如 AI 对话 = 权限校验 → 会话管理 → 检索 → LLM 生成 → 保存）
- **crud** — 纯数据库/向量库操作，无业务逻辑

### RAG 流程

```
用户提问 → 查询改写（多查询扩展）→ 向量检索（ChromaDB similarity_search_with_score）
→ CrossEncoder 重排序 → 格式化为上下文 → LLM 生成回答（流式）→ 保存消息
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | DashScope API Key | — |
| `DATABASE_URL` | MySQL 连接串 | `mysql+aiomysql://root:123456@localhost/rag?charset=utf8mb4` |
