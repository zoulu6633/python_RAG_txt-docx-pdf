"""
检查 ChromaDB 中存储的文档/切片数据。
将 backend 目录加入 sys.path 并切换工作目录，以便正确导入项目模块。
"""
import os
import sys
from collections import defaultdict

# ---- 路径设置 ----
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# ---- 导入项目模块 ----
from services.vector_store import vectorstore

# ---- 获取所有数据 ----
kb_data = vectorstore.get(
    where={"knowledge_base_id": "kb_812649b28fe6"},
    include=["documents", "metadatas"]
)

ids = kb_data.get("ids", [])
documents = kb_data.get("documents", [])
metadatas = kb_data.get("metadatas", [])    

# ---- 按 document_name 分组 ----
grouped = defaultdict(list)
for idx, meta in enumerate(metadatas):
    doc_name = meta.get("document_name", "未知文档")
    grouped[doc_name].append(idx)

# ---- 输出结果 ----
print("=" * 70)
print("ChromaDB 文档切片概览")
print("=" * 70)

for doc_name, indices in sorted(grouped.items()):
    first_meta = metadatas[indices[0]]

    print(f"\n📄 文档名称        : {doc_name}")
    print(f"   切片数量        : {len(indices)}")
    print(f"   知识库 ID       : {first_meta.get('knowledge_base_id', 'N/A')}")
    print(f"   文档 ID         : {first_meta.get('document_id', 'N/A')}")
    print(f"   切片列表:")
    for idx in indices:
        chunk_id = metadatas[idx].get("chunk_id", "N/A")
        content = documents[idx] if documents else ""
        print(f"\n   [{chunk_id}]")
        print(f"   {content}")
    print("-" * 70)

print(f"\n📊 总计: {len(grouped)} 个唯一文档")
