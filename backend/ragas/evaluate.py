"""
RAGAS 评估脚本

流程：
  1. 从 test_data.json 加载测试问题 + ground truth
  2. 对每个问题执行 RAG 检索 → 生成回答
  3. 用 RAGAS 指标评分（faithfulness, answer_relevancy, context_precision, context_recall）
  4. 输出评估结果表格

使用方式：
  1. 确保已安装 ragas:  pip install ragas
  2. 在项目根目录创建 .env 文件，配置 OPENAI_API_KEY
  3. 运行本脚本，按提示输入知识库 ID
"""

import json
import os
import sys

# ── 路径设置 ──
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from dotenv import load_dotenv

load_dotenv()

# ── 1. 加载测试数据 ──
test_data_path = os.path.join(os.path.dirname(__file__), "test_data.json")
with open(test_data_path, "r", encoding="utf-8") as f:
    test_cases = json.load(f)

print(f"已加载 {len(test_cases)} 条测试用例\n")

# ── 2. 获取知识库 ID ──
# 优先从环境变量读取，否则交互式输入
KNOWLEDGE_BASE_ID = os.getenv("RAGAS_KB_ID")
if not KNOWLEDGE_BASE_ID:
    KNOWLEDGE_BASE_ID = input("请输入知识库 ID: ").strip()
    print()

# ── 3. 运行 RAG 流水线 ──
from services.retriever import retrieve_documents, format_context
from services.llm import get_answer

questions = []
answers = []
contexts_list = []
ground_truths = []

for i, case in enumerate(test_cases, start=1):
    q = case["question"]
    gt = case["ground_truth"]

    print(f"[{i}/{len(test_cases)}] 检索中: {q[:50]}...", end=" ", flush=True)

    # 检索
    docs = retrieve_documents(query=q, knowledge_base_id=KNOWLEDGE_BASE_ID)
    ctx = format_context(docs)
    ctx_chunks = [d.page_content for d in docs]

    # 生成
    answer = get_answer(question=q, context=ctx)

    questions.append(q)
    answers.append(answer)
    contexts_list.append(ctx_chunks)
    ground_truths.append(gt)

    print("完成")

# ── 4. RAGAS 评估 ──
print("\n正在运行 RAGAS 评估...")

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts_list,
    "ground_truth": ground_truths,
})

# 复用项目中的 LLM 配置作为评估模型
from langchain_openai import ChatOpenAI

evaluator_llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="qwen3.7-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0,
)

# 使用项目中的 embedding 模型
from langchain_huggingface import HuggingFaceEmbeddings

evaluator_embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5"
)

metrics = [
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
]

# 尝试额外指标
try:
    from ragas.metrics import answer_correctness
    metrics.append(answer_correctness)
except ImportError:
    pass

result = evaluate(
    dataset=dataset,
    metrics=metrics,
    llm=evaluator_llm,
    embeddings=evaluator_embeddings,
)

# ── 5. 输出结果 ──
df = result.to_pandas()
df.insert(0, "question", questions)

print("\n" + "=" * 70)
print("RAGAS 评估结果")
print("=" * 70)
print()

# 逐题输出
for idx, row in df.iterrows():
    print(f"── 问题 {idx+1}: {questions[idx][:60]}...")
    print(f"   回答: {answers[idx][:100]}...")
    for col in metrics:
        col_name = col.name if hasattr(col, "name") else str(col)
        print(f"   {col_name}: {row[col_name]:.4f}")
    print()

print("=" * 70)
print("各指标平均分：")
score_cols = [m.name if hasattr(m, "name") else str(m) for m in metrics]
for col in score_cols:
    mean_val = df[col].mean()
    print(f"  {col:25s}: {mean_val:.4f}")

print("=" * 70)
print("\n评估完成！")
