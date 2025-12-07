"""FastAPI Backend - HUCE Chatbot."""  # Module docstring mô tả tổng quan backend

import warnings  # Thư viện chuẩn để quản lý cảnh báo runtime

warnings.filterwarnings("ignore", category=SyntaxWarning)  # Tắt cảnh báo SyntaxWarning (phát sinh từ underthesea)

import logging  # Dùng để ghi log ứng dụng
import os  # Cung cấp thao tác với hệ điều hành (đường dẫn, thư mục)
import uuid  # Sinh UUID cho từng request
from datetime import datetime, timezone  # datetime để đóng dấu thời gian, timezone để chuẩn hóa UTC
from collections import defaultdict  # defaultdict giúp lưu danh sách theo key IP trong rate limit
from time import time  # Hàm time() dùng đo thời gian epoch phục vụ rate limit

from fastapi import FastAPI, HTTPException, Request, status  # FastAPI core: app, request, HTTP lỗi, mã trạng thái
from fastapi.middleware.cors import CORSMiddleware  # Middleware xử lý CORS
from fastapi.responses import JSONResponse  # Định dạng JSON trả về thủ công

from config import get_cors_origins, get_cors_allow_credentials, get_log_level  # Hàm đọc cấu hình từ config.py
from constants import Validation, ErrorMessage, SuccessMessage  # Các hằng số dùng chung cho validation/thông điệp
from exceptions import ChatbotException, APIException, NLPException, DataException  # Bộ exception tuỳ biến
from models import AdvancedChatRequest, ContextRequest, create_success_response  # Schema Pydantic và helper response
from services.nlp_service import get_nlp_service  # Hàm khởi tạo singleton NLP service

# Logging setup
log_dir = os.path.join(os.path.dirname(__file__), "logs")  # Xác định thư mục logs cạnh file hiện tại
if not os.path.exists(log_dir):  # Nếu thư mục chưa tồn tại
    os.makedirs(log_dir)  # Tạo mới để đảm bảo ghi log được

log_level = getattr(logging, get_log_level(), logging.INFO)  # Đọc log level từ config, fallback INFO
logging.basicConfig(  # Cấu hình logging toàn cục
    level=log_level,  # Mức độ log áp dụng
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Mẫu nội dung log
    handlers=[  # Danh sách nơi nhận log
        logging.FileHandler(os.path.join(log_dir, "chatbot.log"), encoding="utf-8"),  # Ghi file chatbot.log
        logging.StreamHandler(),  # Đồng thời ghi ra stdout để tiện theo dõi console
    ],
)
logger = logging.getLogger(__name__)  # Logger cục bộ cho file này

# FastAPI app
app = FastAPI(title="HUCE Chatbot API", version="1.0.0")  # Khởi tạo ứng dụng FastAPI với title/version

# CORS
app.add_middleware(  # Thêm middleware CORS để kiểm soát nguồn gọi API
    CORSMiddleware,  # Middleware đến từ FastAPI/Starlette
    allow_origins=get_cors_origins(),  # Danh sách origin được phép lấy từ config
    allow_credentials=get_cors_allow_credentials(),  # Cho phép gửi cookie/credential hay không
    allow_methods=["*"],  # Cho phép mọi HTTP method
    allow_headers=["*"],  # Cho phép mọi header
)

# Rate limiting
request_counts = defaultdict(list)  # Lưu danh sách timestamp cho từng IP
RATE_LIMIT_REQUESTS = 100  # Giới hạn tối đa 100 request
RATE_LIMIT_WINDOW = 60  # Trong cửa sổ 60 giây


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host  # Lấy IP client từ request
    current_time = time()  # Thời gian hiện tại dùng để so sánh với cửa sổ giới hạn

    request_counts[client_ip] = [  # Lọc lại danh sách timestamp chỉ giữ request trong khoảng cửa sổ
        req_time for req_time in request_counts[client_ip]  # Duyệt từng timestamp đã lưu
        if current_time - req_time < RATE_LIMIT_WINDOW  # Giữ lại nếu chưa quá 60 giây
    ]

    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:  # Nếu số request đạt giới hạn
        return JSONResponse(  # Trả HTTP 429 với payload chuẩn
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,  # Mã lỗi rate limit
            content={  # Payload thông báo
                "success": False,  # Đánh dấu thất bại
                "error_code": "RATE_LIMIT_EXCEEDED",  # Mã lỗi riêng
                "error_message": "Quá nhiều yêu cầu. Vui lòng thử lại sau.",  # Thông báo người dùng
                "retry_after": RATE_LIMIT_WINDOW,  # Gợi ý thời gian thử lại
            }
        )

    request_counts[client_ip].append(current_time)  # Lưu thêm timestamp cho request hiện tại
    response = await call_next(request)  # Cho phép request tiếp tục xuống stack
    return response  # Trả response về client


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())  # Sinh UUID mới cho mỗi request
    request.state.request_id = request_id  # Lưu vào state để downstream handler truy cập
    response = await call_next(request)  # Tiếp tục middleware chain
    response.headers["X-Request-ID"] = request_id  # Gắn header giúp trace phía client
    return response  # Trả response đã gắn request-id


@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    response = await call_next(request)  # Xử lý request trước rồi mới gắn header bảo mật
    response.headers["X-Content-Type-Options"] = "nosniff"  # Chặn MIME sniffing
    response.headers["X-Frame-Options"] = "DENY"  # Ngăn clickjacking qua iframe
    response.headers["X-XSS-Protection"] = "1; mode=block"  # Yêu cầu trình duyệt bật XSS filter
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # Buộc HTTPS 1 năm
    return response  # Trả response đã thêm header bảo mật


logger.info("HUCE Chatbot API Server đang khởi động...")  # Ghi log lúc server bắt đầu chạy
nlp = get_nlp_service()  # Khởi tạo singleton NLP service (Pipeline + ContextStore)
logger.info("NLP Service đã khởi tạo thành công")  # Log xác nhận NLP sẵn sàng


@app.exception_handler(ChatbotException)
async def chatbot_exception_handler(request: Request, exc: ChatbotException):
    request_id = getattr(request.state, "request_id", None)  # Lấy request-id nếu có để trace log
    logger.error(f"[{request_id}] ChatbotException: {exc.error_code} - {exc.message}")  # Log lỗi chi tiết
    status_code = exc.status_code if isinstance(exc, APIException) else 422 if isinstance(exc, (NLPException,
                                                                                                DataException)) else 500  # Chọn status code tùy loại exception
    return JSONResponse(status_code=status_code, content={  # Trả JSON chuẩn cho lỗi chatbot
        "success": False, "error_code": exc.error_code, "error_message": exc.message,  # Nội dung lỗi chính
        "details": exc.details, "request_id": request_id, "timestamp": datetime.now(timezone.utc).isoformat()
        # Đính kèm chi tiết và timestamp UTC
    })


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)  # Lấy request-id phục vụ trace
    return JSONResponse(status_code=exc.status_code, content={  # Trả lại JSON chuẩn từ HTTPException
        "success": False, "error_code": f"HTTP_{exc.status_code}",  # Ghép mã lỗi chung
        "error_message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),  # Chuẩn hóa thông điệp
        "details": exc.detail if isinstance(exc.detail, dict) else {},
        # Nếu detail là dict thì trả nguyên, ngược lại rỗng
        "request_id": request_id, "timestamp": datetime.now(timezone.utc).isoformat()
        # Thêm request-id và timestamp UTC
    })


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)  # Lấy request-id dù là exception chưa biết
    logger.error(f"[{request_id}] Unhandled exception: {type(exc).__name__} - {str(exc)}",
                 exc_info=True)  # Log chi tiết cùng stacktrace
    return JSONResponse(status_code=500, content={  # Trả response 500 mặc định
        "success": False, "error_code": "INTERNAL_SERVER_ERROR",  # Mã lỗi chung
        "error_message": "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.",  # Thông điệp người dùng
        "details": {"debug_info": str(exc)} if logger.level == logging.DEBUG else {},  # Khi debug mới trả thêm chi tiết
        "request_id": request_id, "timestamp": datetime.now(timezone.utc).isoformat()  # Metadata phục vụ trace
    })


@app.get("/")
async def root():
    """Health check endpoint."""  # Docstring mô tả endpoint gốc
    return create_success_response(message="HUCE Chatbot API đang hoạt động")  # Trả thông điệp API sẵn sàng


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""  # Docstring giải thích endpoint trả trạng thái chi tiết
    try:
        # Check NLP service
        nlp_status = "healthy" if nlp else "unhealthy"  # Kiểm tra biến nlp đã khởi tạo thành công

        # Check data availability
        data_status = "healthy"  # Mặc định dữ liệu ổn
        try:
            from services.csv_service import CSVService  # Import tại chỗ để tránh vòng lặp khi khởi động
            csv_service = CSVService()  # Khởi tạo service đọc CSV
            majors = csv_service.get_majors()  # Thử lấy danh sách ngành
            data_status = "healthy" if len(majors) > 0 else "no_data"  # Nếu rỗng báo no_data
        except Exception as e:
            data_status = f"error: {str(e)}"  # Nếu đọc dữ liệu lỗi thì gắn trạng thái error

        return {  # Trả JSON với tổng quan health
            "status": "healthy",  # Trạng thái chung
            "timestamp": datetime.now(timezone.utc).isoformat(),  # Thời điểm kiểm tra
            "services": {  # Chi tiết từng service con
                "nlp": nlp_status,  # Tình trạng NLP
                "data": data_status,  # Tình trạng đọc dữ liệu
            },
            "version": "1.0.0"  # Phiên bản API
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")  # Ghi log khi toàn bộ health check lỗi
        return JSONResponse(  # Trả HTTP 503 nếu lỗi
            status_code=503,  # Mã dịch vụ không sẵn sàng
            content={  # Payload thông báo lỗi
                "status": "unhealthy",  # Đánh dấu unhealthy
                "timestamp": datetime.now(timezone.utc).isoformat(),  # Thời gian lỗi
                "error": str(e)  # Chi tiết lỗi
            }
        )


@app.post("/chat/context")
async def manage_chat_context(req: ContextRequest):
    """Quản lý context hội thoại - get/set/reset."""  # Docstring mô tả chức năng endpoint
    try:
        session_id = req.session_id or "default"  # Dùng session mặc định nếu client không cung cấp
        if req.action == Validation.ACTION_GET:  # Nhánh lấy context hiện tại
            return create_success_response() | {"context": nlp.get_context(session_id)}  # Trả success + context
        elif req.action == Validation.ACTION_SET:  # Nhánh ghi đè context
            context = req.context or {}  # Đảm bảo payload context không None
            nlp.set_context(session_id, context)  # Ghi context mới vào store
            return create_success_response(message=SuccessMessage.CONTEXT_UPDATED) | {
                "context": context}  # Trả thông báo thành công
        elif req.action == Validation.ACTION_RESET:  # Nhánh reset context
            nlp.reset_context(session_id)  # Xóa context khỏi store
            return create_success_response(message=SuccessMessage.CONTEXT_RESET)  # Thông báo reset thành công
        else:
            raise ValueError(ErrorMessage.INVALID_ACTION)  # Action không hợp lệ => ném ValueError
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))  # Map ValueError sang HTTP 400
    except Exception as e:
        logger.error(f"Error in /chat/context: {str(e)}", exc_info=True)  # Ghi log chi tiết khi lỗi khác xảy ra
        raise HTTPException(status_code=500, detail=ErrorMessage.INTERNAL_ERROR)  # Trả lỗi chung 500


@app.post("/chat/advanced")
async def advanced_chat(req: AdvancedChatRequest):
    """Chat nâng cao - NLP + dữ liệu + context + fallback."""  # Docstring mô tả endpoint chính của chatbot
    try:
        logger.info(
            f"/chat/advanced - Session: {req.session_id} - Message: {req.message[:100]}")  # Log request đến (cắt 100 ký tự)
        session_id = req.session_id or "default"  # Dùng session mặc định khi thiếu
        use_context = req.use_context if req.use_context is not None else True  # Cho phép client tắt context

        current_context = nlp.get_context(session_id) if use_context else {}  # Lấy context hiện tại nếu được phép
        result = nlp.handle_message(req.message, current_context)  # Pipeline NLP xử lý câu hỏi
        analysis, response = result["analysis"], result["response"]  # Tách kết quả phân tích và phản hồi

        logger.info(
            f"/chat/advanced - Intent: {analysis['intent']} (score: {analysis['score']:.2f})")  # Log intent + score

        # Update context
        new_context = nlp.append_history(session_id,
                                         {"message": req.message, "intent": analysis["intent"],
                                          "response": response})  # Lưu lịch sử tin nhắn mới
        current_intent = analysis["intent"]  # Lưu intent hiện tại để xử lý ngữ cảnh
        new_context["last_intent"] = current_intent  # Cập nhật last_intent trong context

        current_entities = analysis["entities"]  # Danh sách entity mới trích xuất
        has_major = any(e.get('label') in ['TEN_NGANH', 'CHUYEN_NGANH', 'MA_NGANH'] for e in
                        current_entities)  # Xem người dùng có nhắc ngành không

        # Nếu không có entity ngành nhưng có thể suy luận từ message, thêm vào entities
        if not has_major and current_intent in ["hoi_nganh_hoc", "hoi_diem_chuan", "hoi_hoc_phi", "hoi_chi_tieu", "hoi_to_hop_mon"]:
            from services.processors.utils import infer_major_from_message
            inferred_major = infer_major_from_message(req.message)
            if inferred_major:
                current_entities = current_entities + [{"label": "TEN_NGANH", "text": inferred_major, "source": "inferred"}]
                has_major = True

        def get_intent_category(intent: str) -> str:
            categories = {"diem_chuan": "diem", "diem": "diem", "hoc_phi": "hoc_phi", "hoc_bong": "hoc_bong",
                          "nganh": "nganh_hoc", "chi_tieu": "chi_tieu", "phuong_thuc": "phuong_thuc",
                          "dieu_kien": "dieu_kien", "thoi_gian": "thoi_gian", "lich_trinh": "thoi_gian",
                          "to_hop": "to_hop", "khoi_thi": "to_hop"}  # Bản đồ keyword -> nhóm context
            for key, cat in categories.items():  # Duyệt từng keyword
                if key in intent:  # Nếu intent chứa keyword
                    return cat  # Trả nhóm tương ứng
            return "other"  # Mặc định nếu không thuộc nhóm nào

        current_category = get_intent_category(current_intent)  # Xác định nhóm cho intent hiện tại
        independent_categories = ["hoc_bong", "dieu_kien", "thoi_gian", "other"]  # Các nhóm không phụ thuộc ngành

        if current_category in independent_categories:  # Nếu intent thuộc nhóm độc lập
            new_context["last_entities"] = current_entities  # Ghi đè entity mới
        elif has_major:  # Nếu intent phụ thuộc nhưng câu hiện tại có tên ngành
            new_context["last_entities"] = current_entities  # Ghi đè entity mới
        else:
            old_major = [e for e in current_context.get("last_entities", []) if
                         e.get('label') in ['TEN_NGANH', 'CHUYEN_NGANH', 'MA_NGANH']]  # Lấy entity ngành trước đó
            new_context[
                "last_entities"] = old_major + current_entities  # Kết hợp ngành cũ với entity mới (giữ mạch hội thoại)

        # Lưu context đã cập nhật vào store để sử dụng cho câu hỏi tiếp theo
        nlp.set_context(session_id, new_context)

        return {"analysis": analysis, "response": response, "context": new_context}  # Trả kết quả cuối cho frontend

    except Exception as e:
        logger.error(f"Error in /chat/advanced: {str(e)}", exc_info=True)  # Log chi tiết khi xử lý thất bại
        raise HTTPException(status_code=500, detail={  # Trả HTTP 500 chuẩn
            "error": "Internal server error",  # Mã lỗi chung
            "message": "Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại.",  # Thông báo thân thiện
        })


if __name__ == "__main__":  # Chỉ chạy block sau khi file được chạy trực tiếp
    import uvicorn  # Import uvicorn để chạy server ASGI

    uvicorn.run(app, host="0.0.0.0", port=8000)  # Khởi động server ở mọi địa chỉ, port 8000
