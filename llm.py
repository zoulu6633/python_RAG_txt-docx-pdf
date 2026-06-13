from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import os
from dotenv import load_dotenv

load_dotenv()
qwen = ChatOpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
    model_name="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)



prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "你是一个专业的文档分析助手。请根据以下提供的背景资料来回答用户的问题。"
    "回答时必须优先提取背景资料中的明确事实、定义、枚举和时间线。"
    "如果背景资料中已经给出列表或分类，必须完整列出，不要省略。"
    "如果背景资料中没有提到相关信息，请回答“在提供的文档中没有找到相关信息”。"
    "回答要求逻辑清晰，尽量保留文档中的关键术语。"""),
    ("user", """

    用户问题：
    {question}

    背景资料：
    {context}
    """)
])


def get_answer(question: str, context: str) -> str:
    chain = prompt | qwen | StrOutputParser()
    response = chain.invoke({ "question": question, "context": context})
    return response
# for chunk in chain.stream({
#     "role": "Python老师",
#     "question": "什么是 FastAPI？"
# }):
#     print(chunk, end="")
