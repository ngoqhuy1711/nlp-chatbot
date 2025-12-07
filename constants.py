"""Constants - Hằng số dùng chung."""  # Docstring mô tả module chứa hằng số


class Intent:
    """Các intent được hỗ trợ."""  # Docstring mô tả nhóm intent
    HOI_DIEM_CHUAN = "hoi_diem_chuan"  # Intent tra cứu điểm chuẩn
    HOI_NGANH_HOC = "hoi_nganh_hoc"  # Intent hỏi thông tin ngành
    HOI_HOC_PHI = "hoi_hoc_phi"  # Intent hỏi học phí
    HOI_HOC_BONG = "hoi_hoc_bong"  # Intent hỏi học bổng
    HOI_CHI_TIEU = "hoi_chi_tieu"  # Intent hỏi chỉ tiêu tuyển sinh
    HOI_TO_HOP_MON = "hoi_to_hop_mon"  # Intent hỏi tổ hợp/khối
    HOI_PHUONG_THUC = "hoi_phuong_thuc"  # Intent hỏi phương thức xét tuyển
    HOI_DIEU_KIEN_XET_TUYEN = "hoi_dieu_kien_xet_tuyen"  # Intent hỏi điều kiện xét tuyển
    HOI_UU_TIEN_XET_TUYEN = "hoi_uu_tien_xet_tuyen"  # Intent hỏi ưu tiên xét tuyển
    HOI_LICH_TUYEN_SINH = "hoi_lich_tuyen_sinh"  # Intent hỏi lịch tuyển sinh
    HOI_KENH_NOP_HO_SO = "hoi_kenh_nop_ho_so"  # Intent hỏi kênh nộp hồ sơ
    HOI_LIEN_HE = "hoi_lien_he"  # Intent hỏi thông tin liên hệ
    FALLBACK = "fallback"  # Intent fallback NLP
    FALLBACK_RESPONSE = "fallback_response"  # Intent khi response đã là fallback

    ALL_INTENTS = [  # Danh sách đầy đủ dùng cho validation
        HOI_DIEM_CHUAN, HOI_NGANH_HOC, HOI_HOC_PHI, HOI_HOC_BONG,
        HOI_CHI_TIEU, HOI_TO_HOP_MON, HOI_PHUONG_THUC,
        HOI_DIEU_KIEN_XET_TUYEN, HOI_UU_TIEN_XET_TUYEN,
        HOI_LICH_TUYEN_SINH, HOI_KENH_NOP_HO_SO, HOI_LIEN_HE,
        FALLBACK, FALLBACK_RESPONSE,
    ]


class Entity:
    """Các entity labels."""  # Docstring mô tả nhóm entity
    MA_NGANH = "MA_NGANH"  # Mã ngành đào tạo
    TEN_NGANH = "TEN_NGANH"  # Tên ngành đào tạo
    KHOI_THI = "KHOI_THI"  # Khối thi truyền thống
    TO_HOP_MON = "TO_HOP_MON"  # Mã tổ hợp xét tuyển
    DIEM_SO = "DIEM_SO"  # Giá trị điểm chung
    DIEM_CHUAN = "DIEM_CHUAN"  # Điểm chuẩn
    DIEM_SAN = "DIEM_SAN"  # Điểm sàn
    NAM_HOC = "NAM_HOC"  # Năm học
    NAM_TUYEN_SINH = "NAM_TUYEN_SINH"  # Alias cho năm tuyển sinh
    PHUONG_THUC_XET_TUYEN = "PHUONG_THUC_XET_TUYEN"  # Phương thức xét tuyển
    PHUONG_THUC_TUYEN_SINH = "PHUONG_THUC_TUYEN_SINH"  # Alias phương thức
    DIEU_KIEN_XET_TUYEN = "DIEU_KIEN_XET_TUYEN"  # Điều kiện xét tuyển

    # Chứng chỉ
    CHUNG_CHI = "CHUNG_CHI"  # Nhãn chung cho chứng chỉ
    CHUNG_CHI_UU_TIEN = "CHUNG_CHI_UU_TIEN"  # Nhãn cho chứng chỉ ưu tiên
    MUC_DO_CHUNG_CHI = "MUC_DO_CHUNG_CHI"  # Band/mức điểm chứng chỉ

    # Học phí & học bổng
    HOC_PHI = "HOC_PHI"  # Mức học phí
    HOC_PHI_CATEGORY = "HOC_PHI_CATEGORY"  # Nhóm chương trình học phí
    HOC_BONG = "HOC_BONG"  # Nhãn chung học bổng
    HOC_BONG_TEN = "HOC_BONG_TEN"  # Tên cụ thể học bổng

    # Thời gian & địa điểm
    THOI_GIAN_TUYEN_SINH = "THOI_GIAN_TUYEN_SINH"  # Thời gian tuyển sinh tổng
    THOI_GIAN_BUOC = "THOI_GIAN_BUOC"  # Thời gian cho từng bước
    KENH_NOP_HO_SO = "KENH_NOP_HO_SO"  # Kênh nộp hồ sơ

    # Liên hệ
    DON_VI_LIEN_HE = "DON_VI_LIEN_HE"  # Đơn vị liên hệ
    DIA_CHI = "DIA_CHI"  # Địa chỉ
    EMAIL = "EMAIL"  # Email liên hệ
    DIEN_THOAI = "DIEN_THOAI"  # Điện thoại bàn
    HOTLINE = "HOTLINE"  # Hotline tuyển sinh
    WEBSITE = "WEBSITE"  # Website chính
    URL = "URL"  # Trường URL phụ


# ==============================================================================
# RESPONSE TYPES - Loại response trả về cho frontend
# ==============================================================================


class ResponseType:
    """Các loại response mà API trả về"""  # Docstring mô tả loại phản hồi

    # Data responses
    MAJOR_INFO = "major_info"  # Thông tin ngành đơn
    MAJOR_LIST = "major_list"  # Danh sách nhiều ngành
    MAJOR_SUGGESTIONS = "major_suggestions"  # Gợi ý ngành
    STANDARD_SCORE = "standard_score"  # Dữ liệu điểm chuẩn
    FLOOR_SCORE = "floor_score"  # Dữ liệu điểm sàn
    TUITION = "tuition"  # Dữ liệu học phí
    SCHOLARSHIPS = "scholarships"  # Dữ liệu học bổng
    QUOTA = "quota"  # Dữ liệu chỉ tiêu
    SCHEDULE = "schedule"  # Dữ liệu lịch tuyển sinh
    APPLY_CHANNEL = "apply_channel"  # Thông tin kênh nộp hồ sơ
    CONDITIONS = "conditions"  # Điều kiện xét tuyển
    CONTACT = "contact"  # Thông tin liên hệ

    # Helper responses
    SCORE_HELP = "score_help"  # Gợi ý hỏi điểm chuẩn đúng
    GENERAL_HELP = "general_help"  # Gợi ý chung
    CLARIFICATION = "clarification"  # Yêu cầu làm rõ thêm
    FALLBACK = "fallback"  # Phản hồi fallback

    # Chart responses (tương lai)
    CHART_DATA = "chart_data"  # Placeholder cho dữ liệu biểu đồ
    COMPARISON = "comparison"  # Placeholder cho so sánh nhiều mục


# ==============================================================================
# VALIDATION CONSTANTS - Các giá trị hợp lệ cho validation
# ==============================================================================


class Validation:
    """Các hằng số dùng cho validation input"""  # Docstring mô tả nhóm validation

    # Điểm số
    MIN_SCORE = 0.0  # Điểm thấp nhất cho phép
    MAX_SCORE = 30.0  # Điểm cao nhất cho phép

    # Năm học
    MIN_YEAR = 2020  # Năm nhỏ nhất có dữ liệu
    MAX_YEAR = 2030  # Năm lớn nhất được hỗ trợ

    # Score types
    SCORE_TYPE_CHUAN = "chuan"  # Mã loại điểm chuẩn
    SCORE_TYPE_SAN = "san"  # Mã loại điểm sàn
    VALID_SCORE_TYPES = [SCORE_TYPE_CHUAN, SCORE_TYPE_SAN]  # Danh sách loại điểm hợp lệ

    # Context actions
    ACTION_GET = "get"  # Hành động đọc context
    ACTION_SET = "set"  # Hành động ghi context
    ACTION_RESET = "reset"  # Hành động reset context
    VALID_ACTIONS = [ACTION_GET, ACTION_SET, ACTION_RESET]  # Danh sách dùng cho validation

    # Số lượng kết quả tối đa
    MAX_RESULTS = 100  # Giới hạn số kết quả trả về
    MAX_SUGGESTIONS = 20  # Giới hạn số gợi ý


# ==============================================================================
# ERROR MESSAGES - Thông báo lỗi tiếng Việt
# ==============================================================================


class ErrorMessage:
    """Các thông báo lỗi chuẩn cho API"""  # Docstring mô tả nhóm thông báo lỗi

    # Validation errors
    INVALID_SCORE = "Điểm số không hợp lệ. Điểm phải từ 0 đến 30."  # Lỗi khi điểm ngoài range
    INVALID_YEAR = "Năm học không hợp lệ. Vui lòng nhập năm từ 2020 đến 2030."  # Lỗi năm
    INVALID_SCORE_TYPE = "Loại điểm không hợp lệ. Chỉ chấp nhận 'chuan' hoặc 'san'."  # Lỗi loại điểm
    INVALID_ACTION = "Hành động không hợp lệ. Chỉ chấp nhận 'get', 'set' hoặc 'reset'."  # Lỗi action context
    MISSING_PARAMETER = "Thiếu tham số bắt buộc: {param}"  # Template lỗi thiếu tham số

    # Data errors
    NO_DATA_FOUND = "Không tìm thấy dữ liệu phù hợp."  # Khi truy vấn không có kết quả
    FILE_NOT_FOUND = "Không tìm thấy file dữ liệu: {filename}"  # Khi thiếu file CSV
    DATA_PARSE_ERROR = "Lỗi đọc dữ liệu từ file: {filename}"  # Khi parse CSV thất bại

    # Server errors
    INTERNAL_ERROR = "Đã xảy ra lỗi nội bộ. Vui lòng thử lại sau."  # Lỗi chung 500
    NLP_ERROR = "Lỗi xử lý ngôn ngữ tự nhiên. Vui lòng thử lại."  # Lỗi pipeline NLP
    DATABASE_ERROR = "Lỗi truy cập dữ liệu. Vui lòng thử lại sau."  # Lỗi nguồn dữ liệu (placeholder)


# ==============================================================================
# SUCCESS MESSAGES - Thông báo thành công tiếng Việt
# ==============================================================================


class SuccessMessage:
    """Các thông báo thành công chuẩn"""  # Docstring mô tả nhóm thông tin thành công

    CONTEXT_RESET = "Đã reset context. Bắt đầu hội thoại mới."  # Thông báo reset context
    CONTEXT_UPDATED = "Đã cập nhật context."  # Thông báo set context
    DATA_FOUND = "Tìm thấy {count} kết quả."  # Thông báo tìm thấy dữ liệu
