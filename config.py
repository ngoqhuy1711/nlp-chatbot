"""Cấu hình cho backend Chatbot HUCE."""  # Docstring mô tả module config

import os  # Thư viện chuẩn dùng đọc biến môi trường và thao tác đường dẫn
from typing import List  # Dùng annotate các hàm trả List[str]

# Đường dẫn
BASE_DIR = os.path.dirname(__file__)  # Thư mục gốc của backend
DATA_DIR = os.path.join(BASE_DIR, "data")  # Đường dẫn tuyệt đối tới thư mục data

# Tham số mặc định
INTENT_THRESHOLD_DEFAULT: float = 0.25  # Ngưỡng score intent mặc định
CONTEXT_HISTORY_LIMIT_DEFAULT: int = 10  # Số lượt hội thoại giữ lại trong context

SERVER_HOST_DEFAULT: str = "0.0.0.0"  # Host default cho server
SERVER_PORT_DEFAULT: int = 8000  # Port default cho server
DEBUG_DEFAULT: bool = False  # Trạng thái debug mặc định
LOG_LEVEL_DEFAULT: str = "INFO"  # Log level mặc định

CORS_ORIGINS_DEFAULT: List[str] = [  # Danh sách origin cho phép mặc định
    "http://localhost:3000",  # Dev server React/Vite
    "http://localhost:8001",  # Cổng dev phụ
    "http://localhost:5173",  # Vite default
    "http://localhost:8080",  # Vue dev server
    "http://127.0.0.1:3000",  # Loopback dạng IP
    "http://127.0.0.1:8001",  # Cổng loopback khác
    "http://127.0.0.1:5173",  # Loopback cho Vite
    "http://127.0.0.1:8080",  # Loopback cho Vue
]
CORS_ALLOW_CREDENTIALS_DEFAULT: bool = True  # Cho phép gửi cookie theo mặc định

MAX_RESULTS_DEFAULT: int = 100  # Giới hạn số dòng dữ liệu trả về mặc định
MAX_SUGGESTIONS_DEFAULT: int = 20  # Giới hạn số gợi ý fallback


# Getter functions
def get_intent_threshold() -> float:
    return float(os.getenv("INTENT_THRESHOLD", INTENT_THRESHOLD_DEFAULT))  # Lấy INTENT_THRESHOLD hoặc dùng default


def get_context_history_limit() -> int:
    """
    Lấy giới hạn độ dài lịch sử hội thoại từ environment hoặc mặc định.

    Returns:
        int: Số câu hỏi tối đa được lưu, mặc định 10
    """
    return int(os.getenv("CONTEXT_HISTORY_LIMIT", CONTEXT_HISTORY_LIMIT_DEFAULT))  # Biến môi trường -> int


def get_server_host() -> str:
    """
    Lấy host cho server từ environment hoặc mặc định.

    Returns:
        str: Host, mặc định "0.0.0.0"
    """
    return os.getenv("SERVER_HOST", SERVER_HOST_DEFAULT)  # Host phục vụ API


def get_server_port() -> int:
    """
    Lấy port cho server từ environment hoặc mặc định.

    Returns:
        int: Port, mặc định 8000
    """
    return int(os.getenv("SERVER_PORT", SERVER_PORT_DEFAULT))  # Port run server


def get_debug_mode() -> bool:
    """
    Lấy debug mode từ environment hoặc mặc định.

    Returns:
        bool: Debug mode, mặc định False
    """
    debug_str = os.getenv("DEBUG", str(DEBUG_DEFAULT)).lower()  # Đọc biến DEBUG rồi chuyển về lowercase
    return debug_str in ("true", "1", "yes", "on")  # Chuẩn hóa sang bool


def get_log_level() -> str:
    """
    Lấy log level từ environment hoặc mặc định.

    Returns:
        str: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL), mặc định INFO
    """
    return os.getenv("LOG_LEVEL", LOG_LEVEL_DEFAULT).upper()  # Trả log level uppercase


def get_cors_origins() -> List[str]:
    """
    Lấy danh sách CORS origins từ environment hoặc mặc định.

    Environment variable CORS_ORIGINS format: "http://localhost:3000,http://localhost:5173"

    Returns:
        List[str]: Danh sách origins được phép
    """
    origins_str = os.getenv("CORS_ORIGINS", None)  # Đọc chuỗi origin nếu có
    if origins_str:
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]  # Split và loại bỏ khoảng trắng
    return CORS_ORIGINS_DEFAULT  # Nếu không có env thì dùng default


def get_cors_allow_credentials() -> bool:
    allow_str = os.getenv("CORS_ALLOW_CREDENTIALS", str(CORS_ALLOW_CREDENTIALS_DEFAULT)).lower()  # Đọc biến bool
    return allow_str in ("true", "1", "yes", "on")  # Chuyển thành bool hợp lệ


def get_max_results() -> int:
    return int(os.getenv("MAX_RESULTS", MAX_RESULTS_DEFAULT))  # Giới hạn số kết quả trả về cho processors


def get_max_suggestions() -> int:
    return int(os.getenv("MAX_SUGGESTIONS", MAX_SUGGESTIONS_DEFAULT))  # Giới hạn số gợi ý fallback
