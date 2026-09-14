# DeskMate — Version Compare Workbench (UI)

UI của lab là **công cụ so sánh phiên bản**, không phải chatbot marketing. Mục đích:
cùng MỘT câu hỏi (hoặc một eval case) → đối chiếu **hành vi tool-calling** giữa các
phiên bản artifact (prompt + tools), để thấy trực quan thay đổi nào tạo khác biệt
đo được (chính là câu chuyện B1/B2 trong REPORT).

## Chạy

Từ thư mục `starter_v0`:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-ui.txt
.venv/Scripts/python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Mở http://localhost:8501. Provider mặc định **OpenRouter / openai/gpt-4o-mini**
(theo tech stack đã chốt của nhóm). Nhập provider/model/API key ở **sidebar**.
API key chỉ giữ trong phiên UI, không ghi vào `.env`/transcript/Git; bỏ trống thì
dùng key từ `.env`. Xem `../TOOL-SETUP.md` để cấu hình provider.

## Ba chế độ

1. **🆚 So sánh 2 version** — chọn Version A và Version B, nhập một câu hỏi, chạy
   trên cả hai. Hiển thị 2 cột: reply + trace tool-calling từng vòng (tên tool,
   arguments, result/error) + hash artifact. Có cảnh báo nếu chuỗi tool-call của
   hai version KHÁC nhau.
2. **🎯 Replay eval case** — chọn dataset (`eval_base`/`eval_group`/`extension`/
   `adversarial`) và một case, xem `input` + `expected`, chạy trên 2 version và
   chấm bằng chính grader của `run_eval` (`evaluate_phase_b`) → badge PASS/FAIL,
   expected vs actual, mismatch. Đây là cách thấy trực quan vì sao v0 fail còn
   version mới pass.
3. **💬 Trò chuyện 1 version** — chạy một câu hỏi trên một version, xem trace đầy đủ.

## Phiên bản so sánh (version discovery)

UI tự phát hiện version từ:
- `artifacts/system_prompt.md` + `artifacts/tools.yaml` → **current · main**
- mỗi thư mục con trong `artifacts/versions/<tên>/` chứa `system_prompt.md` +
  `tools.yaml` → một snapshot (ví dụ `artifacts/versions/v0/` = baseline gốc).

Muốn thêm mốc so sánh (ví dụ v1, v2), tạo thêm thư mục snapshot tương ứng.

## Tái sử dụng runtime (không viết loop mới)

- Chat/compare dùng `chat.run_model_tool_loop` (thực thi nhiều vòng, có kết quả tool thật).
- Replay dùng `agent.HelpdeskAgent.run(..., tool_choice=...)` + `run_eval.evaluate_phase_b`
  — GIỐNG hệt cách `run_eval` chấm, nên PASS/FAIL trên UI khớp với eval evidence.
- Provider factory `make_provider(name, api_key=...)` nhận key riêng của phiên UI;
  CLI/eval không truyền key vẫn dùng env như trước.

## Kiểm chứng

```powershell
.venv/Scripts/python.exe scripts/check_ui.py
```

Smoke check dùng provider giả lập (clarify) với runtime thật — **không gọi API,
không tạo ticket**. Kiểm: 3 mode render, default OpenRouter, version discovery
(current + v0), compare chạy cả 2 version, nút bị khoá khi thiếu key.

Trước khi nộp, chạy compare/replay với provider thật trên artifacts cuối để lấy
evidence. `transcripts/`, `runs/`, `tickets/` mặc định bị Git ignore. Không đưa
API key hoặc dữ liệu thật vào submission.
