import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

MODEL_NAME = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = """
Bạn là trợ lý học tập của trường đại học.

Nhiệm vụ:
- Hỗ trợ sinh viên hiểu bài, ôn tập và tìm thông tin trong tài liệu.
- Hỗ trợ giảng viên xây dựng câu hỏi, bài tập, giáo án và tài liệu giảng dạy.
- Ưu tiên thông tin có trong tài liệu được cung cấp.
- Không tự bịa quy định, lịch học, điểm số hoặc chính sách của nhà trường.
- Nếu tài liệu không chứa câu trả lời, hãy nói rõ:
  "Tôi không tìm thấy thông tin này trong tài liệu được cung cấp."
- Khi có thể, hãy nêu tên mục, chương hoặc số trang chứa thông tin.
- Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu.
"""


def upload_document(file_path: str):
    """Upload tài liệu lên Gemini Files API."""

    return client.files.upload(
        file=file_path,
        config={
            "mime_type": "application/pdf"
        }
    )


def start_chat(document, question: str):
    """Tạo lượt chat đầu tiên, kèm theo tài liệu."""

    interaction = client.interactions.create(
        model=MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION,
        input=[
            {
                "type": "document",
                "uri": document.uri,
                "mime_type": document.mime_type,
            },
            {
                "type": "text",
                "text": question,
            },
        ],
    )

    return interaction


def continue_chat(previous_interaction_id: str, question: str):
    """Tiếp tục cuộc hội thoại trước đó."""

    interaction = client.interactions.create(
        model=MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION,
        input=question,
        previous_interaction_id=previous_interaction_id,
    )

    return interaction


if __name__ == "__main__":
    document = upload_document(
        "input/quy_che_dao_tao.pdf"
    )

    first_response = start_chat(
        document=document,
        question=(
            "Theo tài liệu, sinh viên được phép nghỉ tối đa "
            "bao nhiêu phần trăm số buổi học?"
        ),
    )

    print("Bot:", first_response.output_text)

    second_response = continue_chat(
        previous_interaction_id=first_response.id,
        question="Quy định đó nằm ở mục nào trong tài liệu?",
    )

    print("Bot:", second_response.output_text)