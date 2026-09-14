# AGENTS.md — Rule làm việc cho AI agent (canonical)

File này là **nguồn quy tắc chung** cho mọi AI coding agent làm việc trong repo:
**Google Antigravity, Claude (Claude Code) và OpenAI Codex** đều tuân theo file này.
(`CLAUDE.md` trỏ về file này để tránh lệch nội dung.)

Repo: `Dokhacgiakhoa/K4-Day04-Fast-and-Fourious` (Team **Fast and Fourious**, K4 Day 04).
Đọc file này trước khi thao tác. Áp dụng cho mọi thay đổi code/artifact.

## Quy tắc Git (BẮT BUỘC)

1. **Mỗi feature = 1 branch riêng.** Không gộp nhiều feature vào một branch.
   - Đặt tên branch: `feat/<mô-tả-ngắn>`, `fix/<...>`, `docs/<...>`, hoặc `contrib/<github_username>` cho phần việc cá nhân.
2. **PR LÀ BẮT BUỘC.** Hễ đã push commit lên một branch thì **phải mở đúng 1 Pull Request vào `main`** cho branch đó. Commit/push mà không mở PR là **không hợp lệ** — `main` đã bật ruleset "require pull request", branch không có PR sẽ **không bao giờ được merge** và xem như chưa đóng góp gì.
3. **KHÔNG commit trực tiếp vào `main`.** Nếu đang ở `main`, phải tạo branch mới trước khi commit. (GitHub ruleset chặn push thẳng đối với collaborator.)
4. **AI KHÔNG tự merge vào `main`.** Sau khi mở PR, dừng lại và báo cho Lead ([@Dokhacgiakhoa](https://github.com/Dokhacgiakhoa)). Việc merge do Lead hoặc cơ chế auto-merge của Lead (chỉ merge PR sạch + compile pass) thực hiện, không phải agent tự merge.
5. **Merge KHÔNG squash** — giữ commit cá nhân của từng thành viên (điều kiện chấm điểm).
6. Chỉ push/commit khi người dùng yêu cầu rõ ràng. **Push xong là mở PR ngay**, không để branch lơ lửng.

## Luồng chuẩn cho một feature

```
git switch -c feat/<scope>      # tách branch từ main
# ...thực hiện thay đổi...
git add <file>
git commit -m "type(scope): mô tả"
git push -u origin feat/<scope>
gh pr create --base main        # mở PR, KHÔNG merge
# -> báo Lead duyệt
```

## Commit message

- Format: `type(scope): mô tả ngắn` (type: feat/fix/docs/refactor/test/chore).
- Nếu agent là Claude Code, kết thúc commit message bằng dòng:
  ```
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
  ```
  (Agent khác dùng attribution tương ứng của mình, hoặc bỏ trống.)

## Pull request

- Tiêu đề rõ ràng, mô tả: thay đổi gì, thuộc track nào, file liên quan, cách test.
- @mention thành viên phụ trách track tương ứng (xem [TASKS.md](TASKS.md)).
- Nếu là Claude Code, kết thúc phần mô tả PR bằng:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  ```

## An toàn dữ liệu

- KHÔNG commit `.env`, API key, token, `.venv`, cache, `runs/` chứa secret, `tickets/` (generated), dữ liệu thật.
- Không in API key ra log/screenshot.

## Bối cảnh lab

- Hai artifact chính cần cải thiện: `starter_v0/artifacts/system_prompt.md`, `starter_v0/artifacts/tools.yaml`.
- Phân công & tiến độ: xem [TASKS.md](TASKS.md). Setup: xem [SETUP-NOTES.md](SETUP-NOTES.md).
- UI phải tái sử dụng `run_model_tool_loop` từ `starter_v0/chat.py`, không viết agent loop mới.
