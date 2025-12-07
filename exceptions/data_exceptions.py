from typing import Optional, Dict, Any

from . import ChatbotException


class DataException(ChatbotException):
    def __init__(
            self,
            message: str,
            error_code: str = "DATA_ERROR",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class DataNotFoundError(DataException):
    def __init__(
            self,
            message: str = "Không tìm thấy dữ liệu",
            data_type: Optional[str] = None,
            query_params: Optional[Dict[str, Any]] = None
    ):
        details = {
            "data_type": data_type,
            "query_params": query_params
        }
        super().__init__(
            message,
            error_code="DATA_NOT_FOUND",
            details={k: v for k, v in details.items() if v is not None}
        )


class CSVLoadError(DataException):
    def __init__(
            self,
            message: str = "Lỗi đọc file dữ liệu",
            file_path: Optional[str] = None,
            error_details: Optional[str] = None
    ):
        details = {
            "file_path": file_path,
            "error_details": error_details
        }
        super().__init__(
            message,
            error_code="CSV_LOAD_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


class InvalidMajorError(DataException):
    def __init__(
            self,
            message: str = "Ngành học không hợp lệ",
            major_name: Optional[str] = None,
            major_code: Optional[str] = None,
            suggestions: Optional[list] = None
    ):
        details = {
            "major_name": major_name,
            "major_code": major_code,
            "suggestions": suggestions
        }
        super().__init__(
            message,
            error_code="INVALID_MAJOR",
            details={k: v for k, v in details.items() if v is not None}
        )


class DataValidationError(DataException):
    def __init__(
            self,
            message: str = "Dữ liệu không hợp lệ",
            field: Optional[str] = None,
            value: Optional[Any] = None,
            expected_type: Optional[str] = None
    ):
        details = {
            "field": field,
            "value": value,
            "expected_type": expected_type
        }
        super().__init__(
            message,
            error_code="DATA_VALIDATION_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


__all__ = [
    "DataException",
    "DataNotFoundError",
    "CSVLoadError",
    "InvalidMajorError",
    "DataValidationError"
]
