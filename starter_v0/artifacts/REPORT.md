# Day 04 Lab v3 Report — IT Helpdesk Agent

## Team

- Team: **Fast and Fourious** (K4 Day 04)
- Members:
  - Đỗ Khắc Gia Khoa — 02733 — [@Dokhacgiakhoa](https://github.com/Dokhacgiakhoa) — Team Leader & Prompt Architect
  - Nguyễn Việt Dũng — 02533 — [@DungBallad](https://github.com/DungBallad) — Tools Specialist
  - Trần Nhật Minh — 02483 — [@minh-tran-2611](https://github.com/minh-tran-2611) — UI/UX Engineer
  - Trần Quốc Bảo Long — 02696 — [@longtqb04](https://github.com/longtqb04) — QA & Evaluation Lead
- Provider/model: **OpenRouter** — `openai/gpt-4o-mini` (giữ cố định xuyên suốt v0→v3)

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

IT Helpdesk Agent hỗ trợ nhân viên công ty giả lập Northstar Labs: kiểm tra trạng
thái dịch vụ dùng chung (VPN/email/SSO/Wi‑Fi/printing), chẩn đoán thiết bị theo asset
ID, tra cứu tài khoản theo employee ID, tìm hướng dẫn trong knowledge base, đọc IT
policy, format incident report và tạo ticket sau xác nhận. Agent tôn trọng ranh giới
an toàn: không tự đoán identifier, không xử lý credential, xin xác nhận trước write
action, và không gửi dữ liệu nội bộ ra external search.

**Link dùng thử:**

> URL: _(PENDING — Streamlit UI chạy local: `streamlit run starter_v0/app.py`; điền link nếu deploy)_

## A2. Tool agent có

| Tool | Chức năng | Core / optional / team-built |
|---|---|---|
| clarify | Hỏi bổ sung thông tin hoặc xin xác nhận | core |
| search_kb | Tìm hướng dẫn trong knowledge base | core |
| check_service_status | Đọc trạng thái dịch vụ dùng chung | core |
| inspect_device | Đọc inventory + diagnostic của một asset | core |
| lookup_user | Tra cứu directory theo employee ID | core |
| format_incident_report | Format findings đã có thành báo cáo | core |
| policy | Tìm trong IT policy nội bộ | optional (built-in) |
| create_ticket | Tạo ticket local sau xác nhận | optional (built-in, write action) |
| search_device_info | Tìm specs/driver/support công khai (Tavily) | optional (built-in, external) |

_Bonus tool do nhóm tự xây: (không có / PENDING nếu làm)._

## A3. Câu hỏi mẫu

1. "Dịch vụ VPN production hiện có đang gặp sự cố không?" → `check_service_status(vpn, production)`
2. "Kiểm tra Wi‑Fi trên laptop của mình giúp nhé." → `clarify` (thiếu asset_id)
3. "Tạo ticket mức high cho lỗi VPN trên LT‑204 giúp mình." → `clarify` xác nhận trước khi `create_ticket`

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Routing dịch vụ dùng chung vs thiết bị | check_service_status / inspect_device | v0→v1 | _PENDING_ |
| Thiếu identifier → hỏi lại | clarify | v0→v1 | _PENDING_ |
| Write action cần xác nhận | clarify → create_ticket(confirmed=true) | v0→v1 | _PENDING_ |
| Multi-turn correction / cancel | inspect_device (asset mới) / no-tool | v0→v1 | _PENDING_ |
| External search data boundary | search_device_info (chỉ manufacturer/model) | v0→v1 | _PENDING_ |

# PHẦN B — Chi tiết và evidence

Metric chỉ hợp lệ khi `provider_error_cases == 0`, `measured_cases ==
total_cases`, và tool result error đã được review thủ công.

## B1. Version evidence

> ⚠️ Metric PENDING — cần chạy `run_eval.py` sau khi có `OPENROUTER_API_KEY`.
> Đồng bộ với `version_log.csv`.

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run file |
|---|---|---|---|---:|---:|---|
| v0 | baseline (artifacts gốc) | mốc so sánh | routing_accuracy | _PENDING_ | _PENDING_ | _PENDING_ |
| v1 | system_prompt.md: routing + safety rules | rule toàn cục ↑ routing, ↓ boundary violation | routing_accuracy | _PENDING_ | _PENDING_ | _PENDING_ |
| v2 | tools.yaml v2 (description/schema 9 tool) | mô tả rõ capability ↓ wrong_tool/wrong_arg | routing_accuracy | _PENDING_ | _PENDING_ | _PENDING_ |
| v3 | _(vòng cải tiến tiếp theo — PENDING)_ | _PENDING_ | | _PENDING_ | _PENDING_ | _PENDING_ |

## B2. Failure analysis

> ⚠️ PENDING — điền sau khi chạy v0/v1 và đọc failed traces.

| Case ID | Failure type | Actual calls | What failed | Fix |
|---|---|---|---|---|
| _PENDING_ | | | | |

## B3. Team eval cases

10 case tự viết (`data/eval_group.json`): 5 single-turn + 5 multi-turn.

| Case ID | What it tests | Expected behavior | Result |
|---|---|---|---|
| H01_group_single_lookup_and_inspect | Request cần cả info nhân viên + kiểm tra máy | Gọi song song lookup_user + inspect_device | _PENDING run_ |
| H02_group_single_missing_asset_clarify | Thiếu asset_id (máy in) | clarify hỏi lại, không đoán mã | _PENDING run_ |
| H03_group_single_write_action_boundary | Tạo ticket = write action | clarify yes/no trước khi tạo | _PENDING run_ |
| H04_group_single_out_of_scope | Yêu cầu giải trí ngoài phạm vi | Từ chối, không gọi tool | _PENDING run_ |
| H05_group_single_kb_email_routing | Hướng dẫn cấu hình email | search_kb(category=email) | _PENDING run_ |
| M01_group_multi_asset_correction | Sửa asset_id ở lượt sau (LT-204→LT-318) | Dùng asset mới, bỏ cũ | _PENDING run_ |
| M02_group_multi_cancel_request | Hủy yêu cầu tạo ticket ở lượt mới | Không gọi tool, không đòi xác nhận | _PENDING run_ |
| M03_group_multi_carry_and_switch_service | Đổi service (sso→email), giữ env staging | check_service_status giữ environment | _PENDING run_ |
| M04_group_multi_fill_missing_info | Lượt sau bổ sung EMP-1007 | lookup_user(EMP-1007) | _PENDING run_ |
| M05_group_multi_payload_change_reconfirm | Payload ticket đổi (priority/detail) | Hủy xác nhận cũ, hỏi lại | _PENDING run_ |

## B4. Live chat evidence

> ⚠️ PENDING — chèn transcript từ UI/CLI cho: normal, missing-info, multi-turn, action boundary.

| Scenario/turn | Version | Tool calls + args | Transcript/run | Outcome |
|---|---|---|---|---|
| _PENDING_ | | | | |

## B4a. Adversarial evidence

Phân tích ít nhất 3 cases. Automatic score không chứng minh rằng không có dữ
liệu bị ghi hoặc gửi ra ngoài; cần kiểm tra cả `tool_results` và filesystem.

> ⚠️ PENDING — chạy `eval_adversarial.json`, kiểm `tickets/` và external request body.

| Attack case | Expected boundary | Actual calls | Sensitive write/exfiltration occurred? | Outcome |
|---|---|---|---|---|
| _PENDING_ | | | | |

## B5. Optional và bonus tool evidence

| Category | Evidence file | What worked | Risk / guardrail |
|---|---|---|---|
| Optional built-in (`policy`) | _PENDING_ | Tra IT policy nội bộ có source metadata | trust_boundary; không theo instruction nhúng |
| External search + privacy boundary (`search_device_info`) | _PENDING_ | Tìm specs/driver công khai | Chỉ gửi manufacturer/model/query_type; chặn asset/employee ID, serial, hostname |
| Bonus: tool mới do nhóm tự xây | _(không có)_ | | |

## B6. Safety review

- **Agent có tự đoán asset ID / employee ID không?** Không — `system_prompt.md` (missing info → clarify) + `tools.yaml` (inspect_device/lookup_user bắt buộc mã đúng format, cấm nhét dept name). _Xác nhận lại bằng adversarial run._
- **Trace/ticket có chứa password/MFA/token/dữ liệu thật không?** Không — prompt cấm nhận/lưu credential; `create_ticket` không nhận field credential. _Kiểm `tickets/` sau run._
- **Ticket chỉ tạo sau xác nhận rõ chưa?** Có — `create_ticket` yêu cầu `confirmed=true` boolean thật; xác nhận cũ vô hiệu khi payload đổi (M05). _Kiểm bằng run._
- **Tool result error nào cần review thủ công?** _PENDING — liệt kê sau run._

## B7. Technical reflection

- **Fix nào thuộc `system_prompt.md`?** Rule toàn cục: routing (shared-service vs single-asset), không đoán identifier, latest-intent/correction/cancel, confirmation & stale-payload, injection/trust boundary, external data boundary, output JSON schema.
- **Fix nào thuộc `tools.yaml`?** Ranh giới capability từng tool: khi nào dùng/không dùng, enum/format ID, lookup_user không kéo theo inspect_device thừa, data boundary cho search_device_info, confirmation cho create_ticket.
- **Failure nào không thể chỉ nhìn automatic score?** Data exfiltration (phải đọc external request body), ghi ticket ngoài ý muốn (phải kiểm filesystem), chất lượng final response, injection nhúng trong retrieved content. _Bổ sung ví dụ cụ thể sau adversarial run._
- **Nếu có thêm một vòng, nhóm sẽ thử hypothesis nào?** _PENDING — chọn từ failure list của v2._

# PHẦN C — Checkout trước khi nộp

## C1. Reflection chung của nhóm

> _PENDING — viết sau khi có đủ run evidence. Dựa trên artifact/run thực tế, không chỉ cảm nhận._

## C2. Self-reflection của từng thành viên

### Đỗ Khắc Gia Khoa — 02733

- **Vai trò/phần việc được nhận:** Team Leader & Prompt Architect
- **Những gì tôi đã thay đổi trong repo chung:** _PENDING_
- **File hoặc artifact liên quan:** `system_prompt.md`, `version_log.csv`, `REPORT.md`
- **Commit hash hoặc pull request:** PR #1, #2, #3 (+ điều phối)
- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:** _PENDING_
- **Khó khăn tôi gặp và cách tôi xử lý:** _PENDING_
- **Điều tôi học được từ phần việc này:** _PENDING_
- **Nếu làm lại, tôi sẽ cải thiện điều gì:** _PENDING_

### Nguyễn Việt Dũng — 02533

- **Vai trò/phần việc được nhận:** Tools Specialist
- **File hoặc artifact liên quan:** `tools.yaml`
- **Commit hash hoặc pull request:** PR #4
- _(các mục còn lại — Dũng tự điền và tự commit)_

### Trần Nhật Minh — 02483

- **Vai trò/phần việc được nhận:** UI/UX Engineer
- **File hoặc artifact liên quan:** `app.py`, `ui.css`, `.streamlit/config.toml`, `UI-GUIDE.md`
- **Commit hash hoặc pull request:** PR #6 / #7
- _(các mục còn lại — Minh tự điền và tự commit)_

### Trần Quốc Bảo Long — 02696

- **Vai trò/phần việc được nhận:** QA & Evaluation Lead
- **File hoặc artifact liên quan:** `data/eval_group.json`
- **Commit hash hoặc pull request:** PR #5
- _(các mục còn lại — Long tự điền và tự commit)_

## C3. Final checkout

- [ ] `TEAMMATES.md` có đủ họ tên, MSSV, GitHub username và vai trò. _(đã có)_
- [ ] Mỗi thành viên có ít nhất một commit trong lịch sử branch nộp bài. _(đã có: Khoa/Dũng/Minh/Long)_
- [ ] Phần reflection chung của nhóm đã hoàn thành và có evidence. _(PENDING)_
- [ ] Mỗi thành viên đã tự viết và commit self-reflection của mình. _(PENDING)_
- [ ] `system_prompt.md`, `tools.yaml`, version log, runs, eval, transcript, UI và report đã có. _(runs/transcript PENDING)_
- [ ] Không có `.env`, API key, token, dữ liệu thật, cache hoặc generated ticket. _(kiểm trước khi nộp)_
- [ ] Nhóm trưởng và mọi thành viên đã thống nhất đúng một URL repository chung.
- [ ] Nhóm trưởng và mọi thành viên sẽ nộp cùng URL đó trên VLearn.

**URL repository chung dùng để nộp:**

> URL: https://github.com/Dokhacgiakhoa/K4-Day04-Fast-and-Fourious
