import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "Chưa cấu hình GEMINI_API_KEY trong file .env"
    )

client = genai.Client(api_key=api_key)

DOCUMENT_DIRECTORY = Path(
    "documents/information_technology"
)

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
}


def create_store():
    store = client.file_search_stores.create(
        config={
            "display_name": "faculty-information-technology",
            "embedding_model": "models/gemini-embedding-2",
        }
    )

    print("Đã tạo File Search Store:")
    print(store.name)

    return store


def upload_document(
    store_name: str,
    file_path: Path,
):
    print(f"Đang upload: {file_path.name}")

    operation = (
        client.file_search_stores
        .upload_to_file_search_store(
            file=str(file_path),
            file_search_store_name=store_name,
            config={
                "display_name": file_path.name,
                "custom_metadata": [
                    {
                        "key": "faculty_id",
                        "string_value": (
                            "information-technology"
                        ),
                    },
                    {
                        "key": "faculty_name",
                        "string_value": (
                            "Khoa Công nghệ thông tin"
                        ),
                    },
                    {
                        "key": "scope",
                        "string_value": "faculty",
                    },
                    {
                        "key": "status",
                        "string_value": "active",
                    },
                ],
            },
        )
    )

    while not operation.done:
        print("Đang lập chỉ mục...")
        time.sleep(3)

        operation = client.operations.get(
            operation
        )

    print(f"Hoàn thành: {file_path.name}")


def main():
    if not DOCUMENT_DIRECTORY.exists():
        raise RuntimeError(
            f"Không tìm thấy thư mục: "
            f"{DOCUMENT_DIRECTORY}"
        )

    documents = [
        path
        for path in DOCUMENT_DIRECTORY.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    ]

    if not documents:
        raise RuntimeError(
            "Không tìm thấy tài liệu để upload."
        )

    store = create_store()

    for document in documents:
        upload_document(
            store_name=store.name,
            file_path=document,
        )

    print("\n============================")
    print("Đã hoàn thành lập chỉ mục.")
    print("Thêm dòng sau vào file .env:")
    print(
        f"GEMINI_IT_STORE={store.name}"
    )
    print("============================")


if __name__ == "__main__":
    main()