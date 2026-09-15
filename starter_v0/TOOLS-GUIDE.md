# Hướng Dẫn & Báo Cáo Đóng Góp Track B: Tools Specialist

> **Thành viên phụ trách:** Nguyễn Việt Dũng  
> **MSSV:** 02533  
> **GitHub:** [@DungBallad](https://github.com/DungBallad)  
> **Vai trò:** Tools Specialist (Track B)  
> **Deliverable cốt lõi:** `starter_v0/artifacts/tools.yaml`  

---

## 1. Tổng Quan Nhiệm Vụ (Track B)

Trong bài Lab Day 04 — IT Helpdesk Agent, vai trò **Tools Specialist** chịu trách nhiệm thiết kế, chuẩn hóa và tối ưu toàn bộ giao diện mà Model nhìn thấy thông qua file khai báo công cụ (`tools.yaml`). 

> *"Tool name, description và JSON schema đều là một phần của prompt định hướng hành vi mô hình."*

### Mục tiêu chính đã hoàn thành:
1. **Phân tích lỗi thực nghiệm (Evidence-based Failure Analysis):** Xác định các ca lỗi điển hình ở mốc khởi điểm `v0` (chọn sai tool, trích xuất sai arguments, thiếu thông tin không hỏi lại, vi phạm ranh giới an toàn).
2. **Cải tiến toàn diện 9 công cụ trong `tools.yaml`:**
   - 6 Core Tools: `clarify`, `search_kb`, `check_service_status`, `inspect_device`, `lookup_user`, `format_incident_report`.
   - 3 Advanced Tools: `policy`, `create_ticket`, `search_device_info`.
3. **Bảo đảm ranh giới an toàn & bảo mật (Guardrails & Safety Boundaries):**
   - *Confirmation Boundary:* Chặn đứng việc tự ý gán `confirmed=true` khi tạo ticket; chống giả mạo bằng chuỗi JSON, pseudo-code hoặc role giả danh.
   - *External Data Privacy Boundary:* Chặn tuồn mã tài sản (`LT-xxx`, `DT-xxx`) và mã nhân viên (`EMP-xxxx`) ra ngoài công cụ tìm kiếm web.
4. **Kiểm tra tính toàn vẹn (Definition of Done):**
   - `python -m compileall -q -x "\.venv" .` PASS 100%.
   - Smoke test 9 công cụ chạy thành công không có lỗi runtime.
   - Đồng bộ tên tool giữa `tools.yaml` ↔ `tools/__init__.py` ↔ các bộ eval datasets.

---

## 2. Chi Tiết Các Cải Tiến Trên Từng Tool (`tools.yaml`)

### 2.1. Nhóm Điều Hướng & Thu Thập Thông Tin (Clarify & Directory)
* **`clarify`**:
  - *Hiện trạng v0:* Mô tả sơ sài `"Gửi một câu hỏi cho người dùng."` khiến Agent bỏ qua việc hỏi lại và tự đoán bừa mã tài sản hoặc môi trường.
  - *Cải tiến:* Hướng dẫn Model bắt buộc dùng `clarify(response_type='text')` khi thiếu Asset/Employee ID; dùng `response_type='choice'` khi gặp môi trường ngoài production/staging; và dùng `response_type='yes_no'` khi xin xác nhận tạo ticket.
* **`lookup_user`**:
  - *Cải tiến:* Chuẩn hóa định dạng `employee_id` (bắt buộc dạng `EMP-xxxx`, không nhận tên phòng ban như `Sales`). Ghi rõ kết quả đã có sẵn `assigned_assets` để ngăn chặn Agent gọi thừa tool `inspect_device`.
* **`inspect_device`**:
  - *Cải tiến:* Bắt buộc mã máy chuẩn (`LT-xxx`, `DT-xxx`), cấm truyền tên thiết bị chung chung (`laptop`) hay mã nhân viên (`EMP-xxx`). Bổ sung quy tắc chọn đúng tham số `check` cụ thể (`vpn`, `network`, `security`, `hardware`, `software`) thay vì luôn để mặc định là `all`.

### 2.2. Nhóm Vận Hành & Hướng Dẫn (KB & Service Status)
* **`check_service_status`**:
  - *Cải tiến:* Phân biệt rõ dịch vụ dùng chung toàn công ty (shared service: `vpn`, `email`, `sso`, `wifi`, `printing`) với thiết bị cá nhân. Ràng buộc môi trường chỉ hỗ trợ `production` hoặc `staging`, nghiêm cấm tự ý gán môi trường lạ (`demo`, `lab`, `test`).
* **`search_kb`**:
  - *Cải tiến:* Bổ sung bảng ánh xạ chi tiết cho từng nhóm danh mục `category` (ví dụ: `email` bao gồm cấu hình Outlook, `vpn` bao gồm cài đặt VPN client và certificate macOS/Windows), giúp Agent định tuyến chính xác thay vì để mặc định `all`.

### 2.3. Nhóm Ranh Giới An Toàn & Tác Vụ Ghi (Action & External Tools)
* **`create_ticket`**:
  - *Cải tiến ranh giới bảo mật:* 
    1. Chỉ được gọi khi người dùng con người đã xác nhận rõ ràng bằng lời nói (`confirmed=true`).
    2. Nếu chưa xác nhận, bắt buộc phải dừng lại và gọi `clarify(response_type='yes_no')`.
    3. *Stale Confirmation:* Xác nhận cũ lập tức bị vô hiệu hóa nếu payload (priority, asset_id, summary) bị sửa đổi ở các lượt sau.
    4. *Anti-Spoofing:* Không công nhận chuỗi JSON do user nhập, pseudo-code hàm, hoặc kết quả tool giả lập (`TOOL_RESULTS_JSON`) làm xác nhận.
* **`search_device_info`**:
  - *Cải tiến ranh giới dữ liệu:* Chỉ gửi thông tin công khai (hãng sản xuất, tên model, query_type). Tuyệt đối cấm gửi mã nội bộ ra ngoài web. Nếu người dùng cố tình chèn mã nội bộ và yêu cầu giữ nguyên chuỗi, bắt buộc phải gọi `clarify` để cảnh báo và yêu cầu loại bỏ.
* **`policy`**:
  - *Cải tiến:* Xây dựng hướng dẫn chi tiết cho 6 nhóm `policy_area` (`access_control`, `data_privacy`, `external_tools`, `incident_response`, `service_operations`, `ticketing`), giúp Agent phân loại chính xác các câu hỏi chính sách IT nội bộ.
* **`format_incident_report`**:
  - *Cải tiến:* Ghi rõ chỉ gọi tool khi người dùng yêu cầu xuất/format báo cáo sự cố Markdown; cấm tự động gọi kèm trong các luồng hỏi xác nhận ticket thông thường.

---

## 3. Bằng Chứng Thực Nghiệm & Kết Quả Đo Lường (Benchmark Evidence)

Quá trình tối ưu hóa `tools.yaml` được kiểm chứng qua 4 bài test độc lập với sự cải thiện vượt bậc:

### 3.1. Tiến Trình Nâng Cấp Qua Các Phiên Bản

| Metric Đánh Giá | Baseline `v0` | Cải Tiến `v1` | Hoàn Thiện `v2` / `v3` | Mức Tăng Trưởng |
| :--- | :---: | :---: | :---: | :---: |
| **`eval_base.json` (30 cases)** | 21/30 (70.0%) | 25/30 (83.33%) | **30/30 (100.0%)** | 🟢 **+30.0% (Tuyệt đối)** |
| - *Single-turn Cases (`H01`→`H20`)* | 13/20 (65.0%) | 17/20 (85.0%) | **20/20 (100.0%)** | 🌟 **100% Đạt chuẩn** |
| - *Multi-turn Cases (`M01`→`M10`)* | 8/10 (80.0%) | 8/10 (80.0%) | **10/10 (100.0%)** | 🌟 **100% Đạt chuẩn** |
| - *Tool Routing Accuracy* | 23/30 (76.67%) | 27/30 (90.0%) | **30/30 (100.0%)** | 🟢 **+23.33%** |
| - *Argument Accuracy* | 21/30 (70.0%) | 25/30 (83.33%) | **30/30 (100.0%)** | 🟢 **+30.0%** |
| **`eval_helpdesk_extension.json` (10 cases)** | Chưa chạy | 5/10 (50.0%) | **10/10 (100.0%)** | 🟢 **+50.0% (Tuyệt đối)** |
| **`eval_group.json` (10 cases tự viết)** | Chưa chạy | Chưa chạy | **9/10 (90.0%)** | 🟢 **90% Đạt chuẩn** |
| **`eval_adversarial.json` (12 attacks)** | Chưa chạy | 7/12 (58.33%) | **9/12 (75.0%)** | 🟢 **+16.67%** |

### 3.2. Danh Sách File Run Evidence Được Lưu Trữ:
* `runs/v0_B_base_openai_20260914T183035499911.json`: Baseline khởi điểm (70.0%).
* `runs/v1_B_base_openai_20260914T184358170124.json`: Sửa 4 tool cốt lõi (83.33%).
* `runs/v2_B_base_openai_20260914T193459881975.json`: **Đạt mốc 100% Base Eval (30/30)**.
* `runs/v3_B_extension_openai_20260914T200951123988.json`: **Đạt mốc 100% Extension Eval (10/10)**.
* `runs/v2_B_group_openai_20260914T193646999344.json`: Đạt 90% Team Eval (9/10).
* `runs/v2_B_adversarial_openai_20260914T193521513310.json`: Đạt 75% Adversarial Defense (9/12).

---

## 4. Hướng Dẫn Kiểm Chứng Nhanh (Verification Commands)

Từ thư mục `starter_v0`, đồng đội có thể chạy các lệnh sau để kiểm tra:

### 1. Kiểm tra biên dịch & cú pháp:
```powershell
python -m compileall -q -x "\.venv" .
```

### 2. Kiểm tra Smoke Test toàn bộ công cụ:
```powershell
python -c "from tools import TOOL_FUNCTIONS as T; print({k: bool(v) for k, v in T.items()})"
```

### 3. Tái lập kết quả đánh giá 100% Base & Extension:
```powershell
python run_eval.py --provider openai --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openai --version v3 --suite extension --eval-cases data/eval_helpdesk_extension.json
```

---

## 5. Lịch Sử Git & Đóng Góp Vào Repository Chung

Theo hướng dẫn nộp bài của Lab ([SUBMISSION-GUIDE.md](../SUBMISSION-GUIDE.md)), phần việc của tác giả đã được commit và merge chính thức vào nhánh `main` của repository chung:
- **Nhánh cá nhân:** `Dung-02533-Tools`
- **Pull Request đã merge:** PR #4 (`Merge pull request #4 from Dokhacgiakhoa/Dung-02533-Tools`)
- **Commit hash minh chứng:** `9eaecdc` (*feat(tools): hoàn thiện schema tools.yaml v2...*) và `6fcbd8e`.
