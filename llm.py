from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from models import ChatMessage

import os
import re
from dotenv import load_dotenv

load_dotenv()
qwen = ChatOpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
    model_name="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    streaming=True,
)



prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "你是一个专业的文档分析助手。请根据以下提供的背景资料来回答用户的问题。"
    "回答时必须优先提取背景资料中的明确事实、定义、枚举和时间线。"
    "如果背景资料中已经给出列表或分类，必须完整列出，不要省略。"
    "如果背景资料中没有提到相关信息，请回答“在提供的文档中没有找到相关信息”。"
    "回答要求逻辑清晰，尽量保留文档中的关键术语。"""),
    MessagesPlaceholder(variable_name="history_messages"),

       ("user", """

    用户问题：
    {question}

    背景资料：
    {context}
    """)
])

retrieval_query_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是RAG系统的检索查询改写助手。"
        "你的任务是把用户当前问题和对话历史，改写成适合向量检索的中文查询。"
        "请提炼核心主题、实体、概念、别名、枚举项和限定条件，删除寒暄、请求语气、教学语气。"
        "如果用户是在请求讲解某个知识点，检索查询要改成该知识点本身。"
        "最多输出3行，每行1个检索查询。"
        "不要输出解释，不要编号，不要加项目符号，不要使用Markdown。"
    ),
    MessagesPlaceholder(variable_name="history_messages"),
    (
        "user",
        """
当前用户问题：
{question}
"""
    ),
])

def to_history_messages(history: list[ChatMessage] | None):
    history_messages = []
    for item in history or []:
        if item.role == "user":
            history_messages.append(("user", item.content))
        elif item.role == "assistant":
            history_messages.append(("assistant", item.content))
    return history_messages

def build_retrieval_queries(question: str, history: list[ChatMessage] | None = None) -> list[str]:
    
    chain = retrieval_query_prompt | qwen | StrOutputParser()

    try:
        raw_output = chain.invoke({
            "question": question,
            "history_messages": to_history_messages(history),
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

def get_answer(question: str, context: str, history: list[ChatMessage] | None = None) -> str:
    chain = prompt | qwen | StrOutputParser()
    response = chain.invoke({ 
        "question": question,
         "context": context, 
         "history_messages": to_history_messages(history)})
    return response

def stream_answer(question: str, context: str, history: list[ChatMessage] | None = None):
    chain = prompt | qwen | StrOutputParser()
    for chunk in chain.stream({
        "question": question,
        "context": context,
        "history_messages": to_history_messages(history),

    }):
        yield chunk
