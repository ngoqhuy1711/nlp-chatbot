"""NLP Exceptions - Lỗi xử lý ngôn ngữ tự nhiên."""  # Docstring mô tả module

from typing import Optional, Dict, Any, List  # Type hints cho chi tiết lỗi

from . import ChatbotException  # Base cho mọi exception NLP


class NLPException(ChatbotException):
    """Base exception cho NLP errors."""  # Docstring mô tả lớp cơ sở

    def __init__(
            self,
            message: str,
            error_code: str = "NLP_ERROR",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)  # Ủy quyền cho lớp cha


class IntentNotFoundError(NLPException):
    """Lỗi khi không nhận diện được intent."""  # Docstring mô tả lỗi intent

    def __init__(
            self,
            message: str = "Không thể xác định ý định của câu hỏi",
            confidence: Optional[float] = None,
            detected_intent: Optional[str] = None,
            original_message: Optional[str] = None
    ):
        details = {  # Đính kèm score, intent dự đoán và câu gốc
            "confidence": confidence,
            "detected_intent": detected_intent,
            "original_message": original_message
        }
        super().__init__(
            message,
            error_code="INTENT_NOT_FOUND",
            details={k: v for k, v in details.items() if v is not None}
        )


class EntityExtractionError(NLPException):
    """
    Raised when entity extraction fails or produces invalid results.

    Example:
        >>> if not entities:
        ...     raise EntityExtractionError(
        ...         "No entities extracted from message",
        ...         message=message
        ...     )
    """  # Docstring mô tả lỗi entity

    def __init__(
            self,
            message: str = "Không thể trích xuất thông tin từ câu hỏi",
            original_message: Optional[str] = None,
            expected_entities: Optional[List[str]] = None,
            found_entities: Optional[List[Dict]] = None
    ):
        details = {  # Lưu câu gốc, entity kỳ vọng và entity thực tế
            "original_message": original_message,
            "expected_entities": expected_entities,
            "found_entities": found_entities
        }
        super().__init__(
            message,
            error_code="ENTITY_EXTRACTION_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


class ContextError(NLPException):
    """
    Raised when context management fails.

    This includes:
    - Context retrieval failures
    - Invalid context data
    - Context update failures

    Example:
        >>> if not context or "last_intent" not in context:
        ...     raise ContextError(
        ...         "Invalid context structure",
        ...         session_id=session_id
        ...     )
    """  # Docstring mô tả lỗi context

    def __init__(
            self,
            message: str = "Lỗi xử lý ngữ cảnh hội thoại",
            session_id: Optional[str] = None,
            context_data: Optional[Dict] = None
    ):
        details = {  # Lưu session và context hiện có
            "session_id": session_id,
            "context_data": context_data
        }
        super().__init__(
            message,
            error_code="CONTEXT_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


class PreprocessingError(NLPException):
    """
    Raised when text preprocessing fails.

    Example:
        >>> try:
        ...     tokens = tokenize(text)
        ... except Exception as e:
        ...     raise PreprocessingError(
        ...         "Failed to tokenize text",
        ...         original_text=text
        ...     ) from e
    """  # Docstring mô tả lỗi tiền xử lý

    def __init__(
            self,
            message: str = "Lỗi xử lý văn bản",
            original_text: Optional[str] = None,
            preprocessing_step: Optional[str] = None
    ):
        details = {  # Lưu văn bản gốc và bước đang thực hiện
            "original_text": original_text,
            "preprocessing_step": preprocessing_step
        }
        super().__init__(
            message,
            error_code="PREPROCESSING_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


# Export all NLP exceptions
__all__ = [
    "NLPException",
    "IntentNotFoundError",
    "EntityExtractionError",
    "ContextError",
    "PreprocessingError"
]
