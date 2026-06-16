from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from models import ChatMessage

import os
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

def to_history_messages(history: list[ChatMessage] | None):
    history_messages = []
    for item in history or []:
        if item.role == "user":
            history_messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            history_messages.append(AIMessage(content=item.content))
    return history_messages

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
