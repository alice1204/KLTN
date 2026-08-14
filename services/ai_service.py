import json
import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash"
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def explain_schedule(schedule_result: dict):

    schedule_json = json.dumps(
        schedule_result,
        ensure_ascii=False,
    )

    prompt = f"""
Bạn là trợ lý học vụ cho sinh viên.

Nhiệm vụ:
Giải thích ngắn gọn thời khóa biểu
đã được hệ thống tạo.

Quy tắc:
- Không thay đổi môn.
- Không thay đổi lớp.
- Không thay đổi thời gian.
- Không tự thêm thông tin.
- Nếu reason = retake, nói đây là môn học lại.
- Nếu reason = normal, nói đây là môn đúng tiến độ.
- Nếu reason = early, nói đây là môn học trước.
- Trả lời bằng tiếng Việt.
- Không quá 200 từ.

Dữ liệu:
{schedule_json}
"""

    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        input=prompt,
    )

    return interaction.output_text