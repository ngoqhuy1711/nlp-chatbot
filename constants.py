class Intent:
    HOI_DIEM_CHUAN = "hoi_diem_chuan"
    HOI_NGANH_HOC = "hoi_nganh_hoc"
    HOI_HOC_PHI = "hoi_hoc_phi"
    HOI_HOC_BONG = "hoi_hoc_bong"
    HOI_CHI_TIEU = "hoi_chi_tieu"
    HOI_TO_HOP_MON = "hoi_to_hop_mon"
    HOI_PHUONG_THUC = "hoi_phuong_thuc"
    HOI_DIEU_KIEN_XET_TUYEN = "hoi_dieu_kien_xet_tuyen"
    HOI_UU_TIEN_XET_TUYEN = "hoi_uu_tien_xet_tuyen"
    HOI_LICH_TUYEN_SINH = "hoi_lich_tuyen_sinh"
    HOI_KENH_NOP_HO_SO = "hoi_kenh_nop_ho_so"
    HOI_LIEN_HE = "hoi_lien_he"
    FALLBACK = "fallback"
    FALLBACK_RESPONSE = "fallback_response"

    ALL_INTENTS = [
        HOI_DIEM_CHUAN, HOI_NGANH_HOC, HOI_HOC_PHI, HOI_HOC_BONG,
        HOI_CHI_TIEU, HOI_TO_HOP_MON, HOI_PHUONG_THUC,
        HOI_DIEU_KIEN_XET_TUYEN, HOI_UU_TIEN_XET_TUYEN,
        HOI_LICH_TUYEN_SINH, HOI_KENH_NOP_HO_SO, HOI_LIEN_HE,
        FALLBACK, FALLBACK_RESPONSE,
    ]


class Entity:
    MA_NGANH = "MA_NGANH"
    TEN_NGANH = "TEN_NGANH"
    KHOI_THI = "KHOI_THI"
    TO_HOP_MON = "TO_HOP_MON"
    DIEM_SO = "DIEM_SO"
    DIEM_CHUAN = "DIEM_CHUAN"
    DIEM_SAN = "DIEM_SAN"
    NAM_HOC = "NAM_HOC"
    NAM_TUYEN_SINH = "NAM_TUYEN_SINH"
    PHUONG_THUC_XET_TUYEN = "PHUONG_THUC_XET_TUYEN"
    PHUONG_THUC_TUYEN_SINH = "PHUONG_THUC_TUYEN_SINH"
    DIEU_KIEN_XET_TUYEN = "DIEU_KIEN_XET_TUYEN"

    CHUNG_CHI = "CHUNG_CHI"
    CHUNG_CHI_UU_TIEN = "CHUNG_CHI_UU_TIEN"
    MUC_DO_CHUNG_CHI = "MUC_DO_CHUNG_CHI"

    HOC_PHI = "HOC_PHI"
    HOC_PHI_CATEGORY = "HOC_PHI_CATEGORY"
    HOC_BONG = "HOC_BONG"
    HOC_BONG_TEN = "HOC_BONG_TEN"

    THOI_GIAN_TUYEN_SINH = "THOI_GIAN_TUYEN_SINH"
    THOI_GIAN_BUOC = "THOI_GIAN_BUOC"
    KENH_NOP_HO_SO = "KENH_NOP_HO_SO"

    DON_VI_LIEN_HE = "DON_VI_LIEN_HE"
    DIA_CHI = "DIA_CHI"
    EMAIL = "EMAIL"
    DIEN_THOAI = "DIEN_THOAI"
    HOTLINE = "HOTLINE"
    WEBSITE = "WEBSITE"
    URL = "URL"


class ResponseType:
    MAJOR_INFO = "major_info"
    MAJOR_LIST = "major_list"
    MAJOR_SUGGESTIONS = "major_suggestions"
    STANDARD_SCORE = "standard_score"
    FLOOR_SCORE = "floor_score"
    TUITION = "tuition"
    SCHOLARSHIPS = "scholarships"
    QUOTA = "quota"
    SCHEDULE = "schedule"
    APPLY_CHANNEL = "apply_channel"
    CONDITIONS = "conditions"
    CONTACT = "contact"

    SCORE_HELP = "score_help"
    GENERAL_HELP = "general_help"
    CLARIFICATION = "clarification"
    FALLBACK = "fallback"

    CHART_DATA = "chart_data"
    COMPARISON = "comparison"


class Validation:
    MIN_SCORE = 0.0
    MAX_SCORE = 30.0

    MIN_YEAR = 2020
    MAX_YEAR = 2030

    SCORE_TYPE_CHUAN = "chuan"
    SCORE_TYPE_SAN = "san"
    VALID_SCORE_TYPES = [SCORE_TYPE_CHUAN, SCORE_TYPE_SAN]

    ACTION_GET = "get"
    ACTION_SET = "set"
    ACTION_RESET = "reset"
    VALID_ACTIONS = [ACTION_GET, ACTION_SET, ACTION_RESET]

    MAX_RESULTS = 100
    MAX_SUGGESTIONS = 20


class ErrorMessage:
    INVALID_SCORE = "Điểm số không hợp lệ. Điểm phải từ 0 đến 30."
    INVALID_YEAR = "Năm học không hợp lệ. Vui lòng nhập năm từ 2020 đến 2030."
    INVALID_SCORE_TYPE = "Loại điểm không hợp lệ. Chỉ chấp nhận 'chuan' hoặc 'san'."
    INVALID_ACTION = "Hành động không hợp lệ. Chỉ chấp nhận 'get', 'set' hoặc 'reset'."
    MISSING_PARAMETER = "Thiếu tham số bắt buộc: {param}"

    NO_DATA_FOUND = "Không tìm thấy dữ liệu phù hợp."
    FILE_NOT_FOUND = "Không tìm thấy file dữ liệu: {filename}"
    DATA_PARSE_ERROR = "Lỗi đọc dữ liệu từ file: {filename}"

    INTERNAL_ERROR = "Đã xảy ra lỗi nội bộ. Vui lòng thử lại sau."
    NLP_ERROR = "Lỗi xử lý ngôn ngữ tự nhiên. Vui lòng thử lại."
    DATABASE_ERROR = "Lỗi truy cập dữ liệu. Vui lòng thử lại sau."


class SuccessMessage:
    CONTEXT_RESET = "Đã reset context. Bắt đầu hội thoại mới."
    CONTEXT_UPDATED = "Đã cập nhật context."
    DATA_FOUND = "Tìm thấy {count} kết quả."
