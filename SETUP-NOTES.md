# Setup Notes — K4 Day 04 (dùng chung cho cả nhóm)

Tech stack đã chốt: **Python 3.10+ · OpenRouter · PyYAML · requests · Streamlit** (Tavily chỉ khi dùng `search_device_info`).

Mọi lệnh chạy từ thư mục `starter_v0/`.

## 1. Tạo môi trường (làm 1 lần)

```powershell
cd starter_v0
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

macOS/Linux: thay 2 dòng venv bằng `python3 -m venv .venv` và `source .venv/bin/activate`.

## 2. Điền key OpenRouter

Mở `starter_v0/.env`, điền:

```
OPENROUTER_API_KEY=sk-or-...
```

- Key lấy tại https://openrouter.ai/keys
- **KHÔNG commit `.env`** (đã gitignore). Không in key ra log/screenshot.
- Tavily chỉ cần khi demo `search_device_info`: `TAVILY_API_KEY=tvly-...`

## 3. Verify trước khi tiêu quota

```powershell
python -m compileall -q .
python scripts/preflight_provider.py --provider openrouter
```

Preflight PASS = provider trả structured tool call. Nếu lỗi → xử lý setup trước khi đánh giá prompt.

## 4. Model dùng xuyên suốt

- Mặc định provider: `openai/gpt-4o-mini` (rẻ, tool-calling ổn).
- **Chốt 1 model và giữ cố định v0→v3** để metric so sánh được. Muốn đổi model, thêm `--model <id>` vào lệnh (ví dụ `--model openai/gpt-4o-mini`).

## 5. Lệnh chạy eval

Base (baseline v0 chạy đầu tiên, giữ nguyên artifacts):

```powershell
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json
```

Các suite khác (chạy khi tới phần tương ứng):

```powershell
python run_eval.py --provider openrouter --version v3 --suite group       --eval-cases data/eval_group.json
python run_eval.py --provider openrouter --version v3 --suite extension    --eval-cases data/eval_helpdesk_extension.json
python run_eval.py --provider openrouter --version v3 --suite adversarial  --eval-cases data/eval_adversarial.json
```

Run JSON lưu ở `starter_v0/runs/`. Điều kiện run làm evidence: `provider_error_cases == 0` và `measured_cases == total_cases`.

## 6. Chat CLI / UI

CLI (test thủ công, ghi transcript vào `transcripts/`):

```powershell
python chat.py --provider openrouter --version v0
```

UI (Streamlit) — phải tái sử dụng `run_model_tool_loop` từ `chat.py`:

```powershell
streamlit run app.py
```

## 7. Quy tắc Git cho nhóm

1. Nhóm trưởng fork repo nguồn → đổi tên `KX-DAY04-TenNhom`, cấp quyền/PR cho thành viên.
2. Mỗi người: `git switch -c contrib/<github_username>`, làm phần mình, commit dưới Git identity của mình.
3. Tạo PR vào branch nộp bài. **Merge KHÔNG squash** (giữ commit cá nhân — điều kiện chấm điểm).
4. Kiểm tra mỗi thành viên có ≥1 commit: `git log --format="%h | %an <%ae> | %s"`.

## 8. Không commit

`.env`, API key/token, `.venv`, cache, `runs/` chứa secret, generated tickets (`tickets/`), dữ liệu thật.
