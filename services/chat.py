from langchain_core.documents import Document
from services.retriever import retrieve_documents, serialize_documents
from file_store import save_chat_message, list_recent_chat_messages, ensure_chat_session
from models import ChatResponse, ChatMessage
from llm import get_answer, stream_answer

def format_context(documents: list[Document]) -> str:
    context_blocks = []

    for index, document in enumerate(documents, start=1):
        content = document.page_content.strip()
        if not content:
            continue

        metadata = document.metadata or {}
        source_parts = []

        if metadata.get("file_name"):
            source_parts.append(f"文件: {metadata['file_name']}")
        if metadata.get("chunk_id"):
            source_parts.append(f"片段: {metadata['chunk_id']}")
        if metadata.get("file_id"):
            source_parts.append(f"文件ID: {metadata['file_id']}")

        source_text = " | ".join(source_parts) if source_parts else "来源未知"
        context_blocks.append(f"[参考片段 {index}]\n{source_text}\n{content}")

    return "\n\n".join(context_blocks)

def chat(query: str, session_id: str, user_id: str, file_ids: list[str] | None = None, category_ids: list[str] | None = None):
    ensure_chat_session(session_id, user_id)
    stored_messages = list_recent_chat_messages(session_id, limit=10)
    history_messages = [
    ChatMessage(role=item["role"], content=item["content"])
    for item in stored_messages
    ]
    # 先保存用户消息，避免模型调用失败时整轮丢失
    save_chat_message(session_id, "user", query)
    try:
    
        reranked_results = retrieve_documents(query, file_ids, category_ids, history_messages)
        sources = serialize_documents(reranked_results)
        selected_file_ids = file_ids or []

        if not sources:
            save_chat_message(session_id, "assistant", "在提供的文档中没有找到相关信息。")
            return ChatResponse(
                answer="在提供的文档中没有找到相关信息。",
                sources=[],
                session_id=session_id,
                user_id=user_id,
                source_count=0,
                selected_file_ids=selected_file_ids,
            )

        context = format_context(reranked_results)
    
        answer = get_answer(query, context, history_messages)
        if not answer:
            answer = "在提供的文档中没有找到相关信息。"
        save_chat_message(session_id, "assistant", answer)
    except Exception:
        save_chat_message(session_id, "assistant", "请求失败，请检查模型配置或稍后重试。")
        raise
    

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=session_id,
        user_id=user_id,
        source_count=len(sources),
        selected_file_ids=selected_file_ids,
    )

def chat_stream(query: str, session_id: str, user_id: str, file_ids: list[str] | None = None, category_ids: list[str] | None = None):
    ensure_chat_session(session_id, user_id)
    stored_messages = list_recent_chat_messages(session_id, limit=10)
    history_messages = [
    ChatMessage(role=item["role"], content=item["content"])
    for item in stored_messages
    ]
    # 先保存用户消息，避免模型调用失败时整轮丢失
    save_chat_message(session_id, "user", query)
    try:
        reranked_results = retrieve_documents(query, file_ids, category_ids, history_messages)
        sources = serialize_documents(reranked_results)
        selected_file_ids = file_ids or []

        if not sources:
            fallback_answer = "在提供的文档中没有找到相关信息。"
            save_chat_message(session_id, "assistant", fallback_answer)
            yield {
                "type": "done",
                "answer": fallback_answer,
                "session_id": session_id,
                "user_id": user_id,
                "sources": [],
                "source_count": 0,
                "selected_file_ids": selected_file_ids,
            }
            return

        context = format_context(reranked_results)

        yield {
        "type": "meta",
        "session_id": session_id,
        "user_id": user_id,
        "source_count": len(sources),
        "selected_file_ids": selected_file_ids,
    }
        
        answer=[]

        for chunk in stream_answer(query, context, history_messages):
            answer.append(chunk)
            yield {
                "type": "token",
                "content": chunk,
            }
        final_answer = "".join(answer).strip()
        if not final_answer:
            final_answer = "在提供的文档中没有找到相关信息。"
        save_chat_message(session_id, "assistant", final_answer)

    except Exception:
        save_chat_message(session_id, "assistant", "请求失败，请检查模型配置或稍后重试。")
        raise
    
    yield {
    "type": "done",
    "sources": [item.model_dump() for item in sources],
}