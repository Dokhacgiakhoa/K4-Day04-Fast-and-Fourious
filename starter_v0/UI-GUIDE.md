# Chạy UI DeskMate

Từ thư mục `starter_v0`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Mở http://localhost:8501. Chọn provider, model và artifact version ở sidebar.
API key được đọc từ `.env` theo loader hiện tại của lab (hoặc `DAY04_ENV_FILE`).
Xem `../TOOL-SETUP.md` để cấu hình provider. Khởi động lại app sau khi đổi môi trường.
UI vẫn mở được khi chưa có key; ô gửi chat được bật khi có key.

## Chức năng

- Chat nhiều lượt qua `chat.run_model_tool_loop`, cùng cách giữ history với CLI.
- Hiển thị tool name, arguments, result/error, round và trạng thái xử lý.
- Clarification/confirmation hiển thị trong chat; người dùng trả lời ở lượt kế tiếp.
- Sidebar hiển thị version, prompt/tools hashes và danh sách tools động.
- Transcript tự lưu vào `transcripts/ui_<uuid>.transcript.json` và có nút tải JSON.
- Cuộc trò chuyện mới xóa context trên UI; transcript đã lưu vẫn còn trên máy.
- Khi config hoặc artifacts đổi giữa phiên, UI yêu cầu mở cuộc trò chuyện mới.
- Lỗi provider không tự retry, tránh lặp action; runtime hiện tại không trả partial
  trace nếu exception xảy ra giữa vòng tool. Cần kiểm tra action trước khi gửi lại.

## Phối hợp với nhóm

UI thêm `app.py`, `requirements-ui.txt`, `.streamlit/config.toml`, hướng dẫn và smoke check riêng.
Prompt và Tool tiếp tục sửa các artifact hiện tại. Không hard-code tên tool trong UI.
Giữ contract `run_model_tool_loop` gồm `status`, `assistant_text`, `rounds`, `tool_events`.
Restart app nếu nhóm đổi Python implementation/registry; mở phiên mới nếu đổi artifacts.
Không dùng UI để thay thế evaluator hoặc tự tạo evidence v0–v3.

## Kiểm chứng

```powershell
.\.venv\Scripts\python.exe scripts/check_ui.py
```

Smoke check dùng provider giả lập với runtime thật, không gọi API hay tạo ticket.
Nó kiểm tra chat, clarify và tiếp tục hội thoại, trace, lỗi provider, đổi phiên và
đổi artifacts. Đây là kiểm tra UI, không phải live model evidence để nộp lab.

Trước khi nộp, chạy với provider thật trên artifacts cuối: normal request,
missing-info, multi-turn correction và action confirmation; tải transcript và
đưa evidence đã review vào repo theo hướng dẫn lab. File `transcripts/` mặc định
bị Git ignore. Không đưa API key hoặc dữ liệu thật vào submission.

UI sử dụng [chat elements của Streamlit](https://docs.streamlit.io/develop/api-reference/chat);
smoke check dùng [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
