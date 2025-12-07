"""
Handlers module - Xử lý intent và fallback queries
"""

from .fallback import handle_fallback_query  # Re-export fallback handler
from .intent_handler import handle_intent_query  # Re-export intent handler

__all__ = [
    "handle_intent_query",  # Cho phép import trực tiếp từ services.handlers
    "handle_fallback_query",
]
