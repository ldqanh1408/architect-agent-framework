# Hướng Dẫn Đóng Góp Cho Architect Agent Framework

Cảm ơn bạn đã quan tâm và muốn đóng góp cho **Architect Agent Framework**! Chúng tôi trân trọng mọi đóng góp từ các kiến trúc sư phần mềm, kĩ sư AI và cộng đồng phát triển.

Tài liệu này cung cấp chi tiết về quy trình, tiêu chuẩn code và các bước đóng góp issue, đề xuất kỹ năng (skill), bổ sung adapter và gửi Pull Request (PR).

---

## 📜 Mục Lục

1. [Quy Tắc Ứng Xử (Code of Conduct)](#quy-tắc-ứng-xử-code-of-conduct)
2. [Làm Thế Nào Để Đóng Góp?](#làm-thế-nào-để-đóng-góp)
   - [Báo Lỗi & Issue](#báo-lỗi--issue)
   - [Đề Xuất Tính Năng Mới](#đề-xuất-tính-năng-mới)
   - [Đề Xuất Domain Skill & Task Family Mới](#đề-xuất-domain-skill--task-family-mới)
   - [Bổ Sung Model Adapter Mới](#bổ-sung-model-adapter-mới)
3. [Thiết Lập Môi Trường Phát Triển](#thiết-lập-môi-trường-phát-triển)
4. [Kiến Trúc Dự Án & Tiêu Chuẩn Mã Nguồn](#kiến-trúc-dự-án--tiêu-chuẩn-mã-nguồn)
5. [Quy Trình Gửi Pull Request (PR)](#quy-trình-gửi-pull-request-pr)
6. [Kiểm Tra Cổng Phát Hành (Release Gate)](#kiểm-tra-cổng-phát-hành-release-gate)

---

## 🤝 Quy Tắc Ứng Xử (Code of Conduct)

Chúng tôi cam kết xây dựng một cộng đồng văn minh, tôn trọng và cởi mở. Xin vui lòng giữ thái độ lịch sự, chuyên nghiệp trong mọi trao đổi trên issue, thảo luận và code review.

---

## 💡 Làm Thế Nào Để Đóng Góp?

### Báo Lỗi & Issue (Reporting Issues & Bugs)

Nếu bạn phát hiện lỗi hệ thống, vi phạm contract hoặc sự cố khi chạy CLI/SDK:
* Kiểm tra danh sách Issue hiện có trên GitHub để tránh trùng lặp.
* Tạo Issue mới bằng mẫu **[Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)**.
* Cung cấp thông tin chi tiết:
  - **Tiêu đề rõ ràng**: Tóm tắt ngắn gọn lỗi.
  - **Môi trường**: Hệ điều hành, phiên bản Python, phiên bản Framework.
  - **Các bước tái hiện**: Mã lệnh hoặc script tối giản để kích hoạt lỗi.
  - **Kết quả kỳ vọng vs Kết quả thực tế**.
  - **Log / Traceback chi tiết**: Đầy đủ log lỗi mà không bị ngắt đoạn.

### Đề Xuất Tính Năng Mới (Feature Requests)

Nếu bạn muốn cải tiến động cơ phân rã 2D, quy tắc kiểm tra nhất quán ISO 42010 hoặc CLI:
* Sử dụng mẫu **[Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)**.
* Trình bày lý do kiến trúc, giải pháp đề xuất và tính tương thích ngược.

### Đề Xuất Domain Skill & Task Family Mới

Hệ thống hỗ trợ mở rộng danh mục **110 Domain Skills** và **20 Task Families**:
* Sử dụng mẫu **[Skill Proposal Template](.github/ISSUE_TEMPLATE/skill_proposal.md)**.
* Định nghĩa đầy đủ các khía cạnh ISO 42010, concerns, viewpoints, đầu vào bắt buộc và sản phẩm đầu ra (deliverables).
* Đảm bảo tuân thủ định dạng `skill-contract.yml`.

### Bổ Sung Model Adapter Mới

Bạn muốn tích hợp adapter hỗ trợ cho một dòng mô hình LLM mới (ví dụ: Llama 3.3, Command R+, Qwen 2.5)?
* Sử dụng mẫu **[Adapter Proposal Template](.github/ISSUE_TEMPLATE/adapter_proposal.md)**.
* Định nghĩa định dạng System Prompt (`xml`, `chatml`, `markdown`, `json_schema`), cấu trúc API payload và các tham số mặc định.

---

## 🛠️ Thiết Lập Môi Trường Phát Triển

### 1. Fork & Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/Architect-Agent-Framework.git
cd Architect-Agent-Framework
```

### 2. Tạo Môi Trường Ảo & Cài Đặt Dependencies
```bash
python -m venv .venv
# Trên Linux/macOS:
source .venv/bin/activate
# Trên Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

### 3. Chạy Kiểm Thử Unit Test
```bash
python -m pytest -v
```

---

## 📐 Kiến Trúc Dự Án & Tiêu Chuẩn Mã Nguồn

Mọi mã nguồn đóng góp cần tuân thủ các nguyên tắc thiết kế của dự án:
* **Contract-First Architecture**: Định nghĩa Pydantic schemas chặt chẽ trong `architect_framework/models/`.
* **ISO/IEC/IEEE 42010**: Mọi quyết định kiến trúc phải gắn với viewpoint và concern cụ thể.
* **Cổng Kiểm Tra Phát Hành (Fail-Closed Release Gate)**: Đảm bảo tính toàn vẹn mã băm SHA-256 và SBOM.
* **Type Hints & Docstrings**: Viết đầy đủ gợi ý kiểu dữ liệu và chú thích chuẩn Google docstrings.

---

## 🚀 Quy Trình Gửi Pull Request (PR)

1. **Đặt Tên Branch**: Đặt tên branch rõ ràng phản ánh nội dung:
   - `feature/add-claude-haiku-adapter`
   - `fix/cli-consistency-checker`
   - `skill/add-quantum-arch-domain`
2. **Commit Message**: Tuân thủ chuẩn Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).
3. **Chạy Kiểm Tra Tự Động**:
   ```bash
   # Chạy toàn bộ Unit Tests
   python -m pytest -v

   # Chạy Release Gate Check
   python -m architect_framework.cli.main release-check --skilldir exported_skills
   ```
4. **Tạo Pull Request**: Điền đầy đủ thông tin vào **[Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md)** và liên kết với Issue tương ứng.

---

## 🛡️ Kiểm Tra Cổng Phát Hành (Release Gate)

Trước khi một PR được duyệt hợp nhất vào branch `main`, hệ thống CI/CD sẽ tự động thẩm định:
* 100% Unit Tests vượt qua (`pytest`).
* Thẩm định contract hợp lệ (`validate-contracts`).
* Xác minh tính toàn vẹn chuỗi cung ứng mã nguồn (`release-check`).

Cảm ơn bạn đã đồng hành đóng góp xây dựng hệ chuẩn mở cho Đa Đại Lý Kiến Trúc Phần Mềm!
