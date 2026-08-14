# Frontend chatbot tra cứu quy chế

Phiên bản này đã bỏ:

- Chọn vai trò sinh viên/giảng viên.
- Upload PDF từ phía người dùng.

Tài liệu được giả định đã có sẵn trong backend hoặc kho RAG/File Search.

## Cấu trúc

```text
frontend/
├── index.html
├── style.css
├── app.js
└── README.md
```

## API frontend đang gọi

```http
POST http://127.0.0.1:8000/chat
Content-Type: application/json
```

Request:

```json
{
  "message": "Điều kiện để được xét tốt nghiệp là gì?",
  "document_scope": "all",
  "faculty_id": "all",
  "previous_interaction_id": null
}
```

Response mong đợi:

```json
{
  "answer": "Theo quy chế...",
  "interaction_id": "interaction-id-moi",
  "sources": [
    {
      "document_title": "Quy chế đào tạo",
      "section": "Điều 12",
      "page": 18,
      "scope": "Toàn Học viện"
    }
  ]
}
```

`previous_interaction_id` sẽ là `null` ở câu đầu tiên và mang ID mới
nhất ở các câu hỏi tiếp theo.

## Chạy frontend

```bash
cd frontend
python -m http.server 5500
```

Mở:

```text
http://127.0.0.1:5500
```

## CORS trong FastAPI

```python
from fastapi.middleware.cors import CORSMiddleware

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
```

## Sửa danh sách khoa

Mở `index.html`, tìm:

```html
<select id="facultySelect">
```

Sau đó thay các `<option>` bằng danh sách khoa thực tế của Học viện.
