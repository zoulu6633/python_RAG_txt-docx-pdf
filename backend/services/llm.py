from __future__ import annotations

import os
import re

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from schemas import ChatMessage

load_dotenv()

llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="qwen3.7-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    streaming=True,
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是「团队知识库助手」，一个面向团队的RAG智能问答助手。"
        "你的知识来源仅限于下方提供的「背景资料」。"
        "\n\n"
        "## 回答规则\n"
        "1. **基于资料**：回答须优先提取背景资料中的明确事实、定义、枚举、流程和时间线。"
        "如果资料中已给出列表或分类，必须完整列出，不要自行省略。"
        "2. **无法回答**：如果背景资料中没有相关信息，直接回答「在知识库文档中未找到相关信息」，"
        "不要编造答案，也不要试图用自身知识补充。"
        "3. **逻辑与结构**：回答应逻辑清晰，善用标题、列表、表格等结构化的方式组织内容，"
        "但不要过度冗余。保留文档中的关键术语和原文表述。"
        "4. **对话上下文**：注意结合对话历史中已讨论过的内容，避免重复介绍。"
        "如果用户追问细节，聚焦在背景资料的对应部分展开。"
        "5. **语言**：使用中文回答，专业、简洁、准确。"
        "6. **代码与数据**：如果背景资料包含代码、配置或数据示例，请在回答中按原文格式给出，并附上必要说明。",
    ),
    MessagesPlaceholder(variable_name="history_messages"),
    (
        "user",
        """
用户问题：
{question}

背景资料：
{context}
""",
    ),
])

RETRIEVAL_QUERY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是RAG系统的检索查询改写助手。"
        "你的任务是把用户当前问题和对话历史，改写成适合向量检索的中文查询。"
        "规则："
        "1. 提炼核心主题、实体、概念、别名、枚举项和限定条件，删除寒暄、请求语气、教学语气。"
        "2. 如果用户是在请求讲解某个知识点，检索查询要改成该知识点本身。"
        "3. 如果用户提代词（如「它」「这个」「那个」「上面说的」），需结合历史对话补全为具体实体。"
        "4. 如果问题涉及对比或并列，拆成多个独立查询（如「A 和 B 的区别」→ 分别检索A和B）。"
        "5. 最多输出3行，每行1个检索查询。"
        "6. 不要输出解释，不要编号，不要加项目符号，不要使用Markdown。",
    ),
    MessagesPlaceholder(variable_name="history_messages"),
    (
        "user",
        """
当前用户问题：
{question}
""",
    ),
])


def _to_langchain_messages(history: list[ChatMessage] | None) -> list[tuple[str, str]]:
    result = []
    for item in history or []:
        if item.role == "user":
            result.append(("user", item.content))
        elif item.role == "assistant":
            result.append(("assistant", item.content))
    return result


def build_retrieval_queries(
    question: str,
    history: list[ChatMessage] | None = None,
) -> list[str]:
    chain = RETRIEVAL_QUERY_PROMPT | llm | StrOutputParser()

    try:
        raw_output = chain.invoke({
            "question": question,
            "history_messages": _to_langchain_messages(history),
        })
    except Exception:
        return [question]

    queries: list[str] = []
    seen: set[str] = set()

    for line in raw_output.splitlines():
        normalized = re.sub(r"^\s*[-*0-9.、:：]+\s*", "", line).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        queries.append(normalized)
        if len(queries) >= 3:
            break

    if question not in seen:
        queries.append(question)

    return queries or [question]


def get_answer(
    question: str,
    context: str,
    history: list[ChatMessage] | None = None,
) -> str:
    chain = ANSWER_PROMPT | llm | StrOutputParser()
    response = chain.invoke({
        "question": question,
        "context": context,
        "history_messages": _to_langchain_messages(history),
    })
    return response


def stream_answer(
    question: str,
    context: str,
    history: list[ChatMessage] | None = None,
):
    """生成器：逐 token 产出 LLM 回答片段，用于流式 SSE 输出。"""
    chain = ANSWER_PROMPT | llm | StrOutputParser()
    for chunk in chain.stream({
        "question": question,
        "context": context,
        "history_messages": _to_langchain_messages(history),
    }):
        yield chunk



