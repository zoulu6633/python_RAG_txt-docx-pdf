from interfaces.users import router as users_router
from interfaces.chat import router as chat_router
from interfaces.document import router as document_router
from interfaces.knowledge_base import router as knowledge_base_router

__all__ = ["users_router", "chat_router", "document_router", "knowledge_base_router"]