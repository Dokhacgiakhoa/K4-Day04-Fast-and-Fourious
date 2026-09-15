# Báo cáo phần việc cá nhân — Trần Nhật Minh (02483)

## Thông tin thành viên

- **Họ và tên:** Trần Nhật Minh
- **Mã sinh viên:** 2A202602483
- **GitHub:** [@minh-tran-2611](https://github.com/minh-tran-2611)
- **Vai trò:** UI/UX Engineer
- **Track:** Track C — Giao diện và trải nghiệm người dùng

## Phạm vi phụ trách

Mình phụ trách xây dựng giao diện web cho trợ lý IT Helpdesk DeskMate bằng Streamlit. Mục tiêu là tạo một giao diện dễ sử dụng, giúp người dùng gửi yêu cầu hỗ trợ, theo dõi cách agent xử lý và xem rõ các lần gọi tool. Phần UI vẫn sử dụng chung runtime của nhóm, không tạo một agent loop riêng.

## Các hạng mục đã thực hiện

### 1. Xây dựng giao diện Streamlit

File chính: `starter_v0/app.py`

- Tạo bố cục trang DeskMate theo phong cách SaaS, gồm phần giới thiệu, khu vực kết nối AI, khu vực hội thoại và sidebar.
- Cho phép chọn provider và model, bao gồm Gemini, OpenRouter, OpenAI và Anthropic.
- Cho phép nhập API key dạng password để hạn chế hiển thị trực tiếp trên giao diện.
- Hiển thị trạng thái cấu hình: đã có API key, thiếu model hoặc thiếu artifact version.
- Thêm các câu hỏi mẫu để người dùng bắt đầu nhanh với các nhóm: kết nối, thiết bị và hướng dẫn.
- Thêm nút tạo cuộc trò chuyện mới để reset context khi cần.

### 2. Tích hợp agent runtime có sẵn

UI gọi lại `run_model_tool_loop` từ `starter_v0/chat.py`. Khi người dùng gửi tin nhắn, giao diện truyền vào:

1. system prompt hiện tại;
2. lịch sử hội thoại được giới hạn theo `history_window`;
3. yêu cầu mới nhất của người dùng;
4. danh sách tool được đọc động từ `artifacts/tools.yaml`.

Nhờ vậy, giao diện và CLI dùng chung cách xử lý tool, không bị lệch hành vi giữa hai môi trường.

### 3. Hiển thị trace và trạng thái xử lý

Sau mỗi lượt chat, UI hiển thị:

- nội dung yêu cầu của người dùng;
- câu trả lời cuối của assistant;
- trạng thái lượt xử lý;
- số vòng gọi tool và tổng số tool calls;
- tên từng tool cùng arguments;
- kết quả hoặc lỗi trả về từ tool;
- trường hợp agent đang chờ người dùng bổ sung thông tin hoặc xác nhận;
- cảnh báo khi provider gặp lỗi hoặc đạt giới hạn vòng gọi tool.

Trace được đặt trong vùng mở rộng để giao diện chính vẫn gọn, nhưng người dùng và người kiểm thử vẫn có thể xem đầy đủ bằng chứng xử lý.

### 4. Thiết kế giao diện và cấu hình chạy

Các file liên quan:

- `starter_v0/ui.css`: màu sắc, typography, card, hero section, metrics và trạng thái giao diện.
- `starter_v0/.streamlit/config.toml`: cấu hình mặc định cho Streamlit.
- `starter_v0/requirements-ui.txt`: các dependency cần cho UI.
- `starter_v0/UI-GUIDE.md`: hướng dẫn cài đặt, chạy và kiểm tra UI.
- `starter_v0/scripts/check_ui.py`: smoke test các luồng UI quan trọng.

## Luồng hoạt động tổng quát

```text
Người dùng nhập yêu cầu
        ↓
UI lấy prompt, tool declarations và history
        ↓
run_model_tool_loop xử lý model + tool
        ↓
UI render assistant response và tool trace
        ↓
Cập nhật history và lưu transcript
```

## Kiểm thử đã thực hiện

Chạy UI bằng:

```powershell
cd starter_v0
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Chạy smoke test bằng:

```powershell
cd starter_v0
.\.venv\Scripts\python.exe scripts/check_ui.py
```

Các luồng cần kiểm tra gồm:

- gửi yêu cầu thông thường;
- yêu cầu thiếu Asset ID hoặc Employee ID;
- hội thoại nhiều lượt và sửa lại mã định danh;
- chờ xác nhận trước khi tạo ticket;
- hiển thị tool trace và lỗi provider;
- tạo cuộc trò chuyện mới;
- thay đổi artifact và kiểm tra cảnh báo cấu hình;
- tải transcript JSON.

## Kết quả và đóng góp

Phần UI giúp nhóm có một màn hình demo trực quan thay cho việc chỉ xem log terminal. Người review có thể quan sát được agent đã chọn tool nào, truyền arguments gì, nhận kết quả ra sao và đang ở trạng thái nào. Việc lưu transcript và hiển thị artifact hash cũng giúp kết quả chạy có thể kiểm tra, đối chiếu và tái lập.

## Hướng phát triển

- Bổ sung bộ lọc hoặc nhóm các tool event khi một yêu cầu có nhiều vòng xử lý.
- Cải thiện hiển thị trên màn hình nhỏ.
- Thêm khu vực so sánh transcript giữa các artifact version.
- Tiếp tục kiểm tra UI với các case normal, missing-info, multi-turn và action confirmation trước khi nộp bài.
