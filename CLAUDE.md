# CLAUDE.md — Rule cho Claude Code

**Nguồn quy tắc chung nằm ở [AGENTS.md](AGENTS.md) — đọc và tuân theo file đó trước.**
File này chỉ bổ sung phần riêng cho Claude Code.

## Tóm tắt bắt buộc (chi tiết trong AGENTS.md)

- Mỗi feature = 1 branch (`feat/<scope>`…) → đúng 1 Pull Request vào `main`.
- KHÔNG commit trực tiếp vào `main`. KHÔNG tự merge — mở PR xong dừng lại, báo Lead [@Dokhacgiakhoa](https://github.com/Dokhacgiakhoa) duyệt.
- Merge không squash. Không commit secret/`.env`/`runs/`/`tickets/`.

## Riêng cho Claude Code (attribution)

- Kết thúc commit message bằng:
  ```
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
  ```
- Kết thúc mô tả Pull Request bằng:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  ```

Bối cảnh lab, phân công, setup: xem [AGENTS.md](AGENTS.md), [TASKS.md](TASKS.md), [SETUP-NOTES.md](SETUP-NOTES.md).
