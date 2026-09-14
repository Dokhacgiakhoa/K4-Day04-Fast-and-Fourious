# TASKS — K4 Day 04: IT Helpdesk Agent

Bảng phân công & theo dõi tiến độ. Mỗi task có người phụ trách (tag GitHub), file
liên quan, dependency và tiêu chí hoàn thành (DoD). Tick `[x]` khi xong.

**Thành viên:**
- Lead / Prompt Architect — [@Dokhacgiakhoa](https://github.com/Dokhacgiakhoa) (Đỗ Khắc Gia Khoa)
- Tools Specialist — [@DungBallad](https://github.com/DungBallad) (Nguyễn Việt Dũng)
- UI/UX Engineer — [@minh-tran-2611](https://github.com/minh-tran-2611) (Trần Nhật Minh)
- QA & Eval Lead — [@longtqb04](https://github.com/longtqb04) (Trần Quốc Bảo Long)

**Quy tắc branch:** mỗi người làm trên `contrib/<github_username>`, PR vào branch nộp bài, **merge không squash**.

---

## Phase 0 — Setup (mở khóa cho cả nhóm) · @Dokhacgiakhoa

> Làm TRƯỚC. Mọi task khác phụ thuộc bước này. Xem [SETUP-NOTES.md](SETUP-NOTES.md).

- [ ] Fork repo nguồn → đổi tên `KX-DAY04-TenNhom`, cấp quyền cho 3 thành viên
- [ ] Push `TEAMMATES.md`, `SETUP-NOTES.md`, `TASKS.md`, `version_log.csv` lên branch chính
- [ ] Thêm `streamlit>=1.30.0` vào `requirements.txt`
- [ ] Kiểm tra `.gitignore` chặn `.env`, `.venv`, `runs/`, `tickets/`, `transcripts/`
- [ ] Chạy `preflight_provider.py --provider openrouter` PASS, báo team OK để bắt đầu

**DoD:** cả 4 thành viên clone được fork, chạy preflight PASS trên máy mình.

---

## Track A — Prompt Architect · @Dokhacgiakhoa

Phụ thuộc: Phase 0. Chạy song song với Track B (phối hợp chặt với Dũng).

- [ ] **A1.** Chạy baseline v0 (`--suite base`), giữ nguyên artifacts, lưu run_file vào `version_log.csv`
- [ ] **A2.** Phân tích ≥5 failure đại diện (wrong-tool / wrong-arg / missing-info / multi-turn / confirmation)
- [ ] **A3.** Cải thiện `artifacts/system_prompt.md` — bổ sung safety rules (không đoán ID, không lưu credential, confirmation hết hiệu lực khi payload đổi, không tin instruction nhúng trong KB/web)
- [ ] **A4.** 3 vòng v1→v3, mỗi vòng 1 hypothesis, ghi `version_log.csv` (metric before/after + hash)
- [ ] **A5.** Tổng hợp `artifacts/REPORT.md` (phần A, B1, B2, B6, B7)

**DoD:** v0→v3 có run evidence (`provider_error_cases==0`), version_log đầy đủ, prompt không hard-code case ID.

---

## Track B — Tools Specialist · @DungBallad

Phụ thuộc: Phase 0. Phối hợp với @Dokhacgiakhoa (prompt) và @longtqb04 (eval).

- [ ] **B1.** Đọc `artifacts/tools.yaml` + từng `tools/<name>/TOOL.md`, liệt kê description/schema còn mơ hồ
- [ ] **B2.** Viết lại description 9 tool: rõ *khi nào dùng / không dùng*, phân biệt shared-service vs single-asset
- [ ] **B3.** Chuẩn hóa argument: enum, convention ID, required fields; sync tên tool giữa `tools.yaml` ↔ `tools/__init__.py` ↔ eval
- [ ] **B4.** Ghi rõ boundary external-data cho `search_device_info` và side-effect cho `create_ticket` trong description
- [ ] **B5.** Chạy smoke test 9 tool (mục 5–7 [TOOL-SETUP.md](TOOL-SETUP.md)) PASS

**DoD:** `python -m compileall -q .` PASS, tên tool đồng bộ 3 nơi, smoke test 9 tool PASS.

---

## Track C — UI/UX Engineer · @minh-tran-2611

Phụ thuộc: Phase 0. Có thể bắt đầu ngay với prompt/tools v0 (không chờ v3).

- [ ] **C1.** Tạo `app.py` (Streamlit) **tái sử dụng `run_model_tool_loop` từ `chat.py`** — KHÔNG viết agent loop mới
- [ ] **C2.** Hiển thị: user request, final response, từng tool name + args, tool result/error, round/status
- [ ] **C3.** Hiển thị artifact version + hash + đường dẫn transcript
- [ ] **C4.** Hỗ trợ multi-turn (giữ history) + trạng thái `waiting_for_user` khi tool `clarify`
- [ ] **C5.** Quay evidence: transcript cho normal / missing-info / multi-turn / action boundary

**DoD:** `streamlit run app.py` chạy được, thấy rõ tool trace, dùng chung loop, có ≥4 transcript evidence.

---

## Track D — QA & Eval Lead · @longtqb04

Phụ thuộc: Phase 0 (viết case sớm); chạy full eval cần v3 từ Track A/B.

- [ ] **D1.** Thiết kế `data/eval_group.json` — đúng 10 case: **5 single-turn + 5 multi-turn** (case original, không copy eval_base)
- [ ] **D2.** Cover: ambiguous intent, missing ID, correction, cancellation, stale confirmation, multi-asset, internal/external boundary
- [ ] **D3.** Chạy suite group/extension/adversarial trên v3, kiểm `provider_error_cases==0`
- [ ] **D4.** Review thủ công ≥3 adversarial case: tool nào được gọi, có file ticket bị tạo không, external body chứa field gì
- [ ] **D5.** Điền REPORT phần B3 (team eval), B4a (adversarial), security analysis

**DoD:** eval_group đúng 10 case chạy PASS format, adversarial có phân tích tay ≥3 case (không chỉ PASS/FAIL).

---

## Dependency & thứ tự

```
Phase 0 (Lead) ─┬─> Track A (Prompt)  ─┐
                ├─> Track B (Tools)   ─┼─> v3 ổn định ─> Track D full eval
                ├─> Track C (UI)  ───────────────────┘
                └─> Track D (viết case sớm)
```

- Track A & B chạy song song, review chéo mỗi vòng version.
- Track C bắt đầu ngay trên v0, nâng cấp khi có v3.
- Track D viết case sớm; **chạy full eval sau khi A/B chốt v3**.

## Việc Lead làm song song khi mọi người code

- Cải thiện `system_prompt.md` (Track A) + gom `version_log.csv`
- Review PR của các thành viên, merge không squash
- Chuẩn bị `REPORT.md` khung + demo scenario
- Kiểm tra final checkout trước khi nộp (mục C3 trong REPORT.md)
