import logging
import os
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel, Field


# =========================================================
# 1. CẤU HÌNH
# =========================================================

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_IT_STORE = os.getenv("GEMINI_IT_STORE")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "Chưa cấu hình GEMINI_API_KEY trong file .env"
    )

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# 2. FASTAPI VÀ CORS
# =========================================================

app = FastAPI(
    title="IT Faculty Regulations Chatbot",
    description=(
        "Chatbot tra cứu và giải thích quy định "
        "của Khoa Công nghệ thông tin"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 3. SYSTEM INSTRUCTION
# =========================================================

SYSTEM_INSTRUCTION = """
Bạn là trợ lý tra cứu quy định của Khoa Công nghệ thông tin.

Nhiệm vụ:
- Giải thích các quy định của Khoa Công nghệ thông tin.
- Chỉ sử dụng thông tin tìm được trong kho tài liệu.
- Không tự bổ sung, suy đoán hoặc bịa quy định.

Quy tắc trả lời:
1. Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu.
2. Giải thích nội dung nhưng không làm thay đổi ý nghĩa văn bản.
3. Khi có thể, nêu tên tài liệu, điều, mục hoặc số trang.
4. Nếu không tìm thấy thông tin, phải nói rõ:
   "Tôi không tìm thấy thông tin này trong tài liệu
   Khoa Công nghệ thông tin hiện có."
5. Nếu câu hỏi không thuộc phạm vi Khoa Công nghệ thông tin,
   hãy nói rõ dữ liệu hiện tại chưa hỗ trợ.
6. Không khẳng định văn bản đang còn hiệu lực nếu tài liệu
   không cung cấp thông tin về hiệu lực.
7. Nếu nhiều đoạn tài liệu có dấu hiệu không thống nhất,
   hãy trình bày từng nội dung và không tự kết luận.
"""


# =========================================================
# 4. REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    document_scope: Literal[
        "all",
        "academy",
        "faculty",
    ] = "all"

    faculty_id: str = "all"

    previous_interaction_id: Optional[str] = None


# =========================================================
# 5. HÀM HỖ TRỢ
# =========================================================

def get_store_names(
    document_scope: str,
    faculty_id: str,
) -> list[str]:
    if not GEMINI_IT_STORE:
        raise HTTPException(
            status_code=503,
            detail=(
                "Backend chưa được cấu hình "
                "GEMINI_IT_STORE trong file .env."
            ),
        )

    if document_scope == "academy":
        raise HTTPException(
            status_code=400,
            detail=(
                "Hiện tại hệ thống chưa có kho quy chế chung "
                "của Học viện. Vui lòng chọn quy định của khoa."
            ),
        )

    allowed_faculty_ids = {
        "all",
        "information-technology",
    }

    if faculty_id not in allowed_faculty_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "Hiện tại hệ thống mới hỗ trợ tài liệu "
                "Khoa Công nghệ thông tin."
            ),
        )

    return [GEMINI_IT_STORE]


def build_input_text(request: ChatRequest) -> str:
    scope_name = {
        "all": "Kho tài liệu hiện có",
        "academy": "Quy chế chung của Học viện",
        "faculty": "Quy định riêng của khoa",
    }.get(request.document_scope, request.document_scope)

    faculty_name = {
        "all": "Khoa Công nghệ thông tin",
        "information-technology": (
            "Khoa Công nghệ thông tin"
        ),
    }.get(request.faculty_id, request.faculty_id)

    return (
        f"Phạm vi người dùng chọn: {scope_name}\n"
        f"Khoa áp dụng: {faculty_name}\n"
        "Phạm vi dữ liệu hiện tại chỉ gồm tài liệu "
        "Khoa Công nghệ thông tin.\n\n"
        f"Câu hỏi của người dùng: {request.message}"
    )


def read_value(
    obj: Any,
    key: str,
    default: Any = None,
) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def metadata_to_dict(metadata_items: Any) -> dict:
    if not metadata_items:
        return {}

    if isinstance(metadata_items, dict):
        return metadata_items

    result = {}

    for item in metadata_items:
        key = read_value(item, "key")

        if not key:
            continue

        value = read_value(item, "string_value")

        if value is None:
            value = read_value(item, "numeric_value")

        if value is None:
            value = read_value(item, "bool_value")

        result[key] = value

    return result


def extract_sources(interaction: Any) -> list[dict]:
    sources = []
    seen = set()

    for step in read_value(interaction, "steps", []) or []:
        if read_value(step, "type") != "model_output":
            continue

        for content in read_value(step, "content", []) or []:
            annotations = (
                read_value(content, "annotations", []) or []
            )

            for annotation in annotations:
                if (
                    read_value(annotation, "type")
                    != "file_citation"
                ):
                    continue

                metadata = metadata_to_dict(
                    read_value(
                        annotation,
                        "custom_metadata",
                        [],
                    )
                )

                document_title = (
                    metadata.get("title")
                    or metadata.get("document_title")
                    or read_value(annotation, "file_name")
                    or "Tài liệu tham khảo"
                )

                section = (
                    metadata.get("section")
                    or metadata.get("article")
                    or metadata.get("chapter")
                )

                page = read_value(
                    annotation,
                    "page_number",
                )

                scope = (
                    metadata.get("scope")
                    or metadata.get("faculty_name")
                    or "Khoa Công nghệ thông tin"
                )

                source_reference = read_value(
                    annotation,
                    "source",
                )

                source_key = (
                    document_title,
                    section,
                    page,
                    scope,
                    source_reference,
                )

                if source_key in seen:
                    continue

                seen.add(source_key)

                sources.append(
                    {
                        "document_title": document_title,
                        "section": section,
                        "page": page,
                        "scope": scope,
                        "source": source_reference,
                    }
                )

    return sources


# =========================================================
# 6. ENDPOINT KIỂM TRA
# =========================================================

@app.get("/")
def root():
    return {
        "message": "IT regulations chatbot API đang chạy",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "it_store_configured": bool(GEMINI_IT_STORE),
        "supported_faculties": [
            "information-technology"
        ],
    }


# =========================================================
# 7. ENDPOINT CHAT
# =========================================================

@app.post("/chat")
def chat(request: ChatRequest):
    store_names = get_store_names(
        document_scope=request.document_scope,
        faculty_id=request.faculty_id,
    )

    interaction_args = {
        "model": MODEL_NAME,
        "system_instruction": SYSTEM_INSTRUCTION,
        "input": build_input_text(request),
        "tools": [
            {
                "type": "file_search",
                "file_search_store_names": store_names,
            }
        ],
    }

    if request.previous_interaction_id:
        interaction_args["previous_interaction_id"] = (
            request.previous_interaction_id
        )

    try:
        interaction = client.interactions.create(
            **interaction_args
        )

        return {
            "answer": interaction.output_text,
            "interaction_id": interaction.id,
            "sources": extract_sources(interaction),
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Lỗi khi gọi Gemini API: %s",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể xử lý câu hỏi lúc này. "
                "Hãy kiểm tra Terminal backend "
                "để xem lỗi chi tiết."
            ),
        ) from error
