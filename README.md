# RAG-Project

一个基于 `FastAPI + LangChain + Chroma + Qwen` 的中文 RAG 文档问答项目。

项目支持上传本地文档，自动切块、向量化、入库；用户可以在网页中选择知识库文件，向系统提问，并获得基于检索片段生成的回答与来源证据。

## 项目亮点

- 支持 `txt`、`pdf`、`docx` 文档上传与解析
- 使用 `BAAI/bge-small-zh-v1.5` 进行中文向量化
- 使用 `BAAI/bge-reranker-base` 对召回结果进行重排
- 支持按 `file_id` 过滤检索范围
- 问答接口一次返回 `answer + sources`
- 内置简洁前端页面，可直接演示上传、检索、问答和删除
- 上传文件采用唯一物理路径，避免同名文件覆盖
- 删除文件时同步清理数据库记录、向量库片段和未复用的物理文件

## 适用场景

- 课程作业或毕业设计中的 RAG 原型
- 个人知识库问答系统
- 中文资料检索与问答 Demo
- 简历中的 AI / LLM / RAG 项目展示

## 技术栈

- 后端框架：`FastAPI`
- 文档解析：`LangChain Community`
- 文本切分：`RecursiveCharacterTextSplitter`
- 向量模型：`BAAI/bge-small-zh-v1.5`
- 重排模型：`BAAI/bge-reranker-base`
- 向量数据库：`Chroma`
- 大模型接口：`Qwen-Plus`（DashScope OpenAI Compatible）
- 数据存储：`SQLite`
- 前端：原生 `HTML + CSS + JavaScript`

## 项目结构

```text
RAG-project/
├─ main.py             # FastAPI 入口
├─ routes.py           # 路由：上传、文件列表、删除、问答
├─ services.py         # 文档处理、向量化、检索、重排、删除清理
├─ llm.py              # 大模型调用与提示词
├─ file_store.py       # SQLite 文件记录管理
├─ models.py           # Pydantic 数据模型
├─ static/
│  └─ index.html       # 前端页面
├─ uploads/            # 上传后的物理文件
├─ chroma_db/          # Chroma 持久化目录
├─ app.db              # SQLite 数据库
└─ requirements.txt    # 项目依赖
```

## 核心流程

1. 用户上传文档
2. 系统解析文档内容
3. 文本按固定策略切块
4. 将 chunk 向量化并写入 Chroma
5. 用户输入问题
6. 系统按文件范围召回候选片段
7. 使用 reranker 进行重排
8. 将命中片段拼接为上下文交给大模型生成答案
9. 前端展示答案和参考来源

## 当前功能

- 文档上传与自动入库
- 文件列表查看
- 多文件勾选检索
- 问答结果展示
- 检索来源片段展示
- 删除文件并同步清理索引
- 同名文件唯一化保存

## 环境准备

建议使用：

- `Python 3.10+`
- Windows / macOS / Linux 均可

## 安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

## 环境变量

在项目根目录创建 `.env` 文件，并至少配置以下内容：

```env
OPENAI_API_KEY=你的DashScope兼容API密钥
```

当前项目默认使用：

- 模型：`qwen-plus`
- Base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`

如果你想替换为别的 OpenAI Compatible 模型服务，可以修改 `llm.py`。

## 启动项目

在项目根目录执行：

```bash
uvicorn main:app --reload
```

启动后访问：

- 首页：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- FastAPI 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 页面功能说明

首页提供以下能力：

- 上传文档并自动入库
- 查看已上传文件
- 勾选需要参与检索的文件
- 输入问题并获得回答
- 查看命中的参考片段
- 删除文件并同步清理知识库

## 主要接口

### 1. 上传文件

- 路径：`POST /upload`
- 说明：上传 `txt/pdf/docx` 文件，写入物理目录、数据库和向量库

返回示例：

```json
{
  "file_id": "doc_000001",
  "file_name": "人工智能发展史.txt",
  "path": "C:/.../uploads/doc_000001_人工智能发展史.txt"
}
```

### 2. 获取文件列表

- 路径：`GET /files`
- 说明：返回当前知识库中的文件记录

### 3. 删除文件

- 路径：`DELETE /files/{file_id}`
- 说明：删除文件记录、向量片段，并在没有重复引用时删除物理文件

### 4. 问答

- 路径：`POST /chat`
- 说明：返回答案与来源片段

请求示例：

```json
{
  "query": "文档中提到的机器学习三大范式是什么？",
  "file_ids": ["doc_000004"]
}
```

返回示例：

```json
{
  "answer": "机器学习主要分为三大范式：监督学习、无监督学习、强化学习。",
  "sources": [
    {
      "file_id": "doc_000004",
      "file_name": "人工智能发展史-ai起源.txt",
      "chunk_id": "doc_000004_chunk_001",
      "user_id": "u123",
      "content": "机器学习主要分为三大范式..."
    }
  ],
  "source_count": 1,
  "selected_file_ids": ["doc_000004"]
}
```

## 项目中的一些设计说明

### 1. 为什么物理文件名加了 `file_id`

系统内部保存路径使用：

```text
doc_000001_原文件名.txt
```

这样做的原因是：

- 避免同名文件互相覆盖
- 保留原扩展名，方便文档加载器识别类型
- 页面依然展示原始 `file_name`，不影响用户按文件名选择

### 2. 为什么 `/chat` 直接返回 `sources`

这样前端只需要一次请求，就能拿到：

- 最终答案
- 命中的来源片段
- 片段数量

这比“先问答，再单独取 chunk”更适合演示和产品化。

### 3. 为什么删除时还要判断物理文件是否被复用

如果不同记录引用了同一路径，直接删物理文件可能导致其他记录失效。

当前逻辑会：

- 先删向量数据
- 再删数据库记录
- 最后判断该物理路径是否仍被其他记录引用

只有在没有剩余引用时，才真正删除磁盘文件。

## 已知限制

- 当前 `user_id` 为固定值 `u123`，还不是真正的多用户系统
- 没有会话历史与上下文记忆
- 没有批量删除接口
- 没有权限控制和登录系统
- 还没有自动化测试
- 对异常处理和运行状态提示还可以继续增强

## 后续可优化方向

- 增加用户登录与多知识库隔离
- 增加批量上传 / 批量删除
- 增加会话历史记录
- 增加 BM25 + 向量检索的混合检索
- 增加引用高亮与命中定位
- 增加评估集与自动化测试
- 优化 chunk 策略与 prompt
- 支持本地大模型或更多 API 服务

## 简历描述示例

可以在简历中描述为：

> 基于 FastAPI、LangChain、Chroma 和 Qwen 实现中文 RAG 文档问答系统，支持文档上传、向量检索、重排、来源引用展示与文件级知识库管理，完成从文档入库到问答生成的完整闭环。

## 说明

如果本地启动时报依赖或模型加载问题，请优先检查：

- `requirements.txt` 是否已完整安装
- `.env` 中的 `OPENAI_API_KEY` 是否正确
- 首次运行时 HuggingFace 模型是否成功下载

