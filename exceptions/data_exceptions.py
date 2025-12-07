"""Data Exceptions - Lỗi xử lý dữ liệu."""  # Docstring mô tả module lỗi dữ liệu

from typing import Optional, Dict, Any  # Type hints cho chi tiết lỗi

from . import ChatbotException  # Base exception chung


class DataException(ChatbotException):
    """Base exception cho data errors."""  # Docstring mô tả lớp cơ sở

    def __init__(
            self,
            message: str,
            error_code: str = "DATA_ERROR",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)  # Ủy quyền cho ChatbotException


class DataNotFoundError(DataException):
    """Lỗi khi không tìm thấy dữ liệu."""  # Docstring mô tả trường hợp không có dữ liệu

    def __init__(
            self,
            message: str = "Không tìm thấy dữ liệu",
            data_type: Optional[str] = None,
            query_params: Optional[Dict[str, Any]] = None
    ):
        details = {  # Ghi nhận loại dữ liệu và tham số truy vấn
            "data_type": data_type,
            "query_params": query_params
        }
        super().__init__(
            message,
            error_code="DATA_NOT_FOUND",
            details={k: v for k, v in details.items() if v is not None}  # Bỏ trường None
        )


class CSVLoadError(DataException):
    """
    Raised when CSV file loading fails.

    Example:
        >>> try:
        ...     data = pd.read_csv(csv_path)
        ... except Exception as e:
        ...     raise CSVLoadError(
        ...         f"Failed to load CSV: {csv_path}",
        ...         file_path=csv_path
        ...     ) from e
    """  # Docstring mô tả tình huống lỗi đọc CSV

    def __init__(
            self,
            message: str = "Lỗi đọc file dữ liệu",
            file_path: Optional[str] = None,
            error_details: Optional[str] = None
    ):
        details = {  # Lưu đường dẫn file và lỗi nguồn
            "file_path": file_path,
            "error_details": error_details
        }
        super().__init__(
            message,
            error_code="CSV_LOAD_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


class InvalidMajorError(DataException):
    """
    Raised when major name/code is invalid.

    Example:
        >>> major_data = get_major_info(major_name)
        >>> if not major_data:
        ...     raise InvalidMajorError(
        ...         "Ngành không hợp lệ",
        ...         major_name=major_name
        ...     )
    """  # Docstring mô tả lỗi khi ngành không tồn tại

    def __init__(
            self,
            message: str = "Ngành học không hợp lệ",
            major_name: Optional[str] = None,
            major_code: Optional[str] = None,
            suggestions: Optional[list] = None
    ):
        details = {  # Ghi nhận tên/mã ngành và gợi ý thay thế
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
    """
    Raised when data validation fails.

    Example:
        >>> if not validate_score(score):
        ...     raise DataValidationError(
        ...         "Điểm số không hợp lệ",
        ...         field="score",
        ...         value=score
        ...     )
    """  # Docstring mô tả lỗi dữ liệu không hợp lệ

    def __init__(
            self,
            message: str = "Dữ liệu không hợp lệ",
            field: Optional[str] = None,
            value: Optional[Any] = None,
            expected_type: Optional[str] = None
    ):
        details = {  # Lưu thông tin trường sai, giá trị và type mong đợi
            "field": field,
            "value": value,
            "expected_type": expected_type
        }
        super().__init__(
            message,
            error_code="DATA_VALIDATION_ERROR",
            details={k: v for k, v in details.items() if v is not None}
        )


# Export all data exceptions
__all__ = [
    "DataException",
    "DataNotFoundError",
    "CSVLoadError",
    "InvalidMajorError",
    "DataValidationError"
]
