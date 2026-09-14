# Context bàn giao giữa các agent

Cập nhật: 2026-09-14. File này ghi lại phạm vi đã thống nhất và trạng thái bàn giao;
luôn kiểm tra code/Git hiện tại trước khi tiếp tục vì các thành viên có thể đã cập nhật repo.

## Mục tiêu và phạm vi của người dùng

- Đây là lab IT Helpdesk Agent. Nhóm của người dùng chia 4 role: Prompt, UI, Eval, Tool.
- Người dùng phụ trách **UI** và đã yêu cầu dựng UI ngay trên starter hiện có.
- Người dùng đã xác nhận lại rằng phần vừa thực hiện chỉ là UI và phần kết nối
  cần thiết với runtime starter, không phải hoàn thành toàn bộ lab.
- Khi tiếp tục công việc UI, giữ thay đổi trong phạm vi UI. Không tự mở rộng sang
  tối ưu prompt, sửa tool/evaluator hoặc làm phần việc của thành viên khác.
  Yêu cầu mới rõ ràng của người dùng có thể thay đổi phạm vi này.
- Không suy ra từ file bàn giao này rằng cần tự spawn agent hoặc thực hiện toàn bộ
  các công việc còn lại của nhóm.

## Đọc gì trước

- `README.md`: yêu cầu đầu ra chính thức của lab.
- `LAB-GUIDE.md`: quy trình gợi ý, không phải thứ tự bắt buộc.
- `SUBMISSION-GUIDE.md`: quy định repo chung và bằng chứng đóng góp.
- `starter_v0/UI-GUIDE.md`: cách chạy, chức năng và giới hạn của UI.

## Phần UI đã thực hiện

UI tên **DeskMate**, dùng Streamlit, có giao diện tiếng Việt.

| File | Nội dung |
|---|---|
| `starter_v0/app.py` | Chat UI, session state, gọi runtime, hiển thị trace và xuất transcript |
| `starter_v0/requirements-ui.txt` | Dependencies UI, bao gồm requirements starter và Streamlit |
| `starter_v0/.streamlit/config.toml` | Theme sáng, màu giao diện và tắt usage telemetry |
| `starter_v0/scripts/check_ui.py` | Smoke check UI với AppTest và provider giả lập |
| `starter_v0/UI-GUIDE.md` | Hướng dẫn chạy và tích hợp |

UI hỗ trợ:

- Chọn provider (`openrouter`, `openai`, `anthropic`, `gemini`), model và version.
- Chat nhiều lượt, giới hạn history/tool rounds và tạo cuộc trò chuyện mới.
- Hiển thị tool names, arguments, result/error, từng round và trạng thái trả lời.
- Hiển thị câu hỏi bổ sung/xác nhận khi runtime trả `waiting_for_user`.
- Hiển thị artifact version cùng prompt/tools hashes và danh sách tools động.
- Tự lưu transcript JSON; có nút tải transcript trong sidebar.
- Báo thiếu API key, lỗi đọc artifacts, lỗi provider hoặc lỗi lưu transcript.
- Yêu cầu phiên mới khi config hoặc artifacts thay đổi giữa hội thoại.

Trong lần triển khai UI này, **không sửa** system prompt, tool declarations,
tool implementations/registry, agent runtime, providers, evaluator hoặc eval datasets.

## Interface tích hợp cần giữ

UI import và dùng trực tiếp các thành phần starter:

- `chat.run_model_tool_loop`, `trim_history`, `write_transcript`, `now_iso`,
  `ROOT`, `ARTIFACTS_DIR`.
- `providers.make_provider` và các thuộc tính provider `default_model`, `api_key_env`.
- `tools.load_tool_declarations`, `to_openai_tools`.
- `versioning.build_artifact_version`, `artifact_version_dict`.

Lời gọi runtime hiện tại:

```python
run_model_tool_loop(
    provider=provider,
    messages=messages,
    tools=tools,
    model=model,
    max_tool_rounds=max_tool_rounds,
)
```

Kết quả UI đang tiêu thụ:

```text
status: answered | waiting_for_user | max_tool_rounds
assistant_text: str
rounds: [{round, assistant_text, tool_calls, tool_results}]
tool_calls: [{name, args}]                 # nằm trong mỗi round
tool_results: [{tool, args, result}]       # nằm trong mỗi round
tool_events: [{tool, args, result}]        # tổng hợp cả lượt
```

UI tự ghi `provider_error` khi runtime ném exception; đây không phải trạng thái
trả về bình thường của `run_model_tool_loop`.

- Đọc prompt từ `starter_v0/artifacts/system_prompt.md` và declarations từ
  `starter_v0/artifacts/tools.yaml`; không copy/hard-code chúng vào UI.
- Render tool theo dữ liệu runtime, không rẽ nhánh theo danh sách tên tool cố định.
- Tái sử dụng loop hiện tại, không viết agent loop thứ hai trong UI.
- API key dùng loader starter: `.env` hoặc `DAY04_ENV_FILE`. Không nhập key vào code.
- UI giữ prompt/tools/config của mỗi phiên; khi artifacts đổi, tạo phiên mới.
- Sau khi đổi Python implementation/registry, restart app để nạp code mới.
- Nếu task yêu cầu đổi interface chung, cập nhật các consumer liên quan và ghi rõ
  thay đổi cho nhóm; không âm thầm làm UI/CLI/eval dùng contract khác nhau.

## Phối hợp với các role khác

| Role | Phần việc chính | Liên quan đến UI |
|---|---|---|
| Prompt | `artifacts/system_prompt.md` | UI nạp artifact mới khi mở phiên mới |
| Tool | `artifacts/tools.yaml`, implementation/registry khi cần | Giữ schema và registry đồng bộ; UI hiển thị tools động |
| Eval | Team cases, runs, version log, phân tích failures | UI cung cấp chat/transcript, không thay thế evaluator |
| UI | Các file UI liệt kê phía trên | Kiểm tra tích hợp và lấy transcript trên artifacts cuối |

Các role có thể làm song song nhưng cần tích hợp và kiểm chứng theo từng vòng.
Merge không tự chứng minh rằng prompt/tools/UI kết hợp đúng. Viết tool mới là
bonus theo README, không bắt buộc để hoàn thành core lab.

## Chạy và kiểm tra

Chạy các lệnh dưới đây từ `starter_v0/` bằng PowerShell.
Môi trường `.venv` đã được tạo trên máy tại lần bàn giao; máy khác cần tạo/cài lại.

```powershell
# Chỉ cần khi chưa có môi trường hoặc cần cài dependencies:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt

# Chạy UI local:
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.headless true

# Smoke check không gọi API:
.\.venv\Scripts\python.exe scripts/check_ui.py
```

Địa chỉ mặc định: `http://127.0.0.1:8501`.
Một server đã được khởi động lúc bàn giao, nhưng **không giả định nó vẫn còn chạy**.
Kiểm tra trước khi mở thêm server; không dừng tiến trình lạ để lấy port.

Kết quả đã xác minh ngày 2026-09-14:

- Kiểm tra cú pháp `app.py` và `scripts/check_ui.py`: pass.
- Smoke check AppTest: pass cho chat, clarify/context, trace/tool error,
  provider error, lưu transcript, reset, đổi artifacts và thiếu key.
- Smoke check cũng xác minh UI rerun không gọi lại provider/tool.
- Endpoint `/_stcore/health`: `ok`; trang gốc server: HTTP 200.
- `git diff --check`: pass tại thời điểm bàn giao.

Đây là kiểm tra tích hợp UI với provider giả lập và runtime thật, **không phải
live model evidence**, không chứng minh chất lượng prompt/tool hay hoàn thành lab.
Chưa kiểm thử chat bằng provider thật trong phần việc này.

## Giới hạn và công việc tiếp theo

- Tool trace xuất hiện sau khi một lượt hoàn tất, chưa stream từng tool event.
- History theo cơ chế CLI starter: giữ các cặp user/assistant text, không bổ sung
  cơ chế memory mới trong UI.
- Nếu provider lỗi sau khi tool đã chạy, runtime hiện tại không trả partial trace.
  UI báo giới hạn này và không tự retry để tránh lặp action; đừng coi lỗi provider
  là bằng chứng rằng action chưa xảy ra.
- Reset chỉ xóa context UI; transcript đã lưu vẫn tồn tại.
- Transcript lưu ở `starter_v0/transcripts/ui_<uuid>.transcript.json`, mặc định
  bị Git ignore. Review rồi đưa evidence cần nộp vào repo theo hướng dẫn lab.
- Khi nhóm chốt artifacts, cần chạy provider thật cho normal request, missing-info,
  multi-turn/correction và action confirmation, rồi lấy transcript làm evidence.
- Các phần eval v0–v3, adversarial review, report và reflection vẫn là công việc
  của nhóm; không đánh dấu hoàn thành dựa trên UI smoke check.

## Git và bảo toàn công việc

- Khi tạo file bàn giao này, 5 file UI phía trên vẫn là **untracked**, chưa commit.
  Kiểm tra `git status` hiện tại; không giả định trạng thái đó còn đúng.
- Giữ mọi thay đổi của người dùng/thành viên khác, kể cả file chưa commit.
- Không tự commit/push/merge chỉ vì đọc file này; làm theo yêu cầu đang có của người dùng.
- Không đưa `.env`, keys/tokens, `.venv`, cache, generated tickets hoặc dữ liệu thật vào Git.
- Submission yêu cầu commit đóng góp của từng thành viên trong branch nộp.
  Mỗi người tự viết và commit self-reflection; không viết thay hoặc tạo bằng chứng giả.
- Khi bàn giao tiếp, ghi rõ file đã đổi, kiểm tra đã chạy và phần chưa kiểm chứng.
