from typing import Optional, Dict, Any, List

from . import ChatbotException


class NLPException(ChatbotException):
    def __init__(
            self,
            message: str,
            error_code: str = "NLP_ERROR",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class IntentNotFoundError(NLPException):
    def __init__(
            self,
            message: str = "Không thể xác định ý định của câu hỏi",
            confidence: Optional[float] = None,
            detected_intent: Optional[str] = None,
            original_message: Optional[str] = None
    ):
        details = {
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
    def __init__(
            self,
            message: str = "Không thể trích xuất thông tin từ câu hỏi",
            original_message: Optional[str] = None,
            expected_entities: Optional[List[str]] = None,
            found_entities: Optional[List[Dict]] = None
    ):
        details = {
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
    def __init__(
            self,
            message: str = "Lỗi xử lý ngữ cảnh hội thoại",
            session_id: Optional[str] = None,
            context_data: Optional[Dict] = None
    ):
        details = {
            "session_id": session_id,
            "context_data": context_data
        }
        super().__init__(
            message,
            error_code="CONTEXT_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


class PreprocessingError(NLPException):
    def __init__(
            self,
            message: str = "Lỗi xử lý văn bản",
            original_text: Optional[str] = None,
            preprocessing_step: Optional[str] = None
    ):
        details = {
            "original_text": original_text,
            "preprocessing_step": preprocessing_step
        }
        super().__init__(
            message,
            error_code="PREPROCESSING_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


__all__ = [
    "NLPException",
    "IntentNotFoundError",
    "EntityExtractionError",
    "ContextError",
    "PreprocessingError"
]
