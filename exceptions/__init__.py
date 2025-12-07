"""
Custom Exceptions for Chatbot HUCE
====================
Exception Hierarchy:

All custom exceptions inherit from ChatbotException base class.
This module defines the exception hierarchy for the chatbot system.

"""  # Docstring giải thích module exception
from typing import Optional, Dict, Any  # Type hints dùng cho thuộc tính details


class ChatbotException(Exception):
    """Base exception for all chatbot-specific errors."""  # Docstring mô tả base class

    def __repr__(self) -> str:
        """Developer-friendly representation."""  # Docstring mô tả __repr__
        return f"{self.error_code}: {self.message}"  # Hiển thị mã lỗi + thông điệp

    def __str__(self) -> str:
        """String representation of the exception."""  # Docstring mô tả __str__
        if self.details:  # Nếu có details
            return f"{self.error_code}: {self.message} (Details: {self.details})"  # Hiển thị kèm details
        return f"{self.error_code}: {self.message}"  # Nếu không có details chỉ in mã + thông điệp

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses.

        Returns:
            Dictionary with error information
        """  # Docstring mô tả to_dict
        return {
            "error_code": self.error_code,  # Trả mã lỗi
            "error_message": self.message,  # Trả thông điệp lỗi
            "details": self.details,  # Trả chi tiết lỗi
        }

    def __init__(
            self,
            message: str,
            error_code: str = "CHATBOT_ERROR",
            details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize ChatbotException.

        Args:
            message: Error message for humans
            error_code: Error code for machines (default: CHATBOT_ERROR)
            details: Additional context (optional)
        """  # Docstring mô tả constructor
        super().__init__(message)  # Gọi constructor Exception gốc
        self.details = details or {}  # Lưu dictionary details (mặc định rỗng)
        self.error_code = error_code  # Lưu mã lỗi chuẩn hóa
        self.message = message  # Lưu thông điệp lỗi để dùng lại


# Import all exception classes for easy access
from .nlp_exceptions import (  # noqa: E402  # Import cụ thể để re-export
    NLPException,
    IntentNotFoundError,
    EntityExtractionError,
    ContextError,
    PreprocessingError,
)
from .data_exceptions import (  # noqa: E402
    DataException,
    DataNotFoundError,
    CSVLoadError,
    InvalidMajorError,
    DataValidationError,
)
from .api_exceptions import (  # noqa: E402
    APIException,
    ValidationError,
    RateLimitError,
    AuthenticationError,
    ResourceNotFoundError,
)

# Export all exceptions
__all__ = [  # Danh sách export khi dùng from exceptions import *
    # Base
    "ChatbotException",
    # NLP
    "NLPException",
    "IntentNotFoundError",
    "EntityExtractionError",
    "ContextError",
    "PreprocessingError",
    # Data
    "DataException",
    "DataNotFoundError",
    "CSVLoadError",
    "InvalidMajorError",
    "DataValidationError",
    # API
    "APIException",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
    "ResourceNotFoundError",
]
