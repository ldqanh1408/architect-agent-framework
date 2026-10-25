# Cài bản alpha cục bộ

[English](INSTALL.md) · [Tiếng Việt](INSTALL.vi.md)

Bản bàn giao là **2.0.0**, trạng thái **NOT_QUALIFIED**. Dùng source hoặc wheel đi kèm; chưa có công bố package, tag hay marketplace từ lần bàn giao này. Kiểm thử trên tài khoản Claude/Codex thật, nền tảng native và passkey vật lý được ghi riêng trong sổ ngoại lệ kiểm thử con người.

Tại thư mục source, chuẩn bị Python và console:

```bash
uv sync --frozen --all-extras
npm ci --ignore-scripts
npm run build:console
export ARCHITECT_PYTHON="$PWD/.venv/bin/python"
```

Hoặc cài wheel đi kèm vào môi trường riêng. Thay đường dẫn bằng vị trí artifact đã giải nén:

```bash
python3 -m venv /path/to/aaf-env
/path/to/aaf-env/bin/python -m pip install '/path/to/architect_agent_framework-2.0.0-py3-none-any.whl[console,sdd]'
export ARCHITECT_PYTHON=/path/to/aaf-env/bin/python
```

Các lệnh trên dùng shell và filesystem POSIX. Chưa qualify thực thi Windows native. Giữ host bundle ở vị trí đã giải nén. Cấu hình cơ chế plugin cục bộ của host tới `plugins/architect-agent-framework`; các manifest Claude/Codex đi kèm trỏ vào đó. Làm theo quy trình cài cục bộ của host đang sử dụng. Kiểm thử launcher cục bộ không chứng nhận cài đặt trên tài khoản thật.

Kiểm tra interpreter và launcher (nếu đang đứng trực tiếp tại thư mục gốc của gói plugin độc lập, thay `plugins/architect-agent-framework/scripts/architect_runtime.py` bằng `scripts/architect_runtime.py`):

```bash
"$ARCHITECT_PYTHON" -m architect_framework.cli.main --help
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap --help
```

Khởi tạo một thư mục spec mới, trống:

```bash
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap sdd host-init ./my-spec --workspace-id my-project --reviewer owner
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap console serve ./my-spec --enroll
```

Người dùng tự chạy enrollment trong terminal của mình và xác nhận fingerprint. Chữ ký cho phép dispatch task và quyết định chấp nhận tài liệu là hai bước riêng. Agent không được đăng ký, trust hay ký thay người dùng. Mở thư mục không tự migration. Đọc [hướng dẫn core](docs/GUIDE-SDD-CORE.md) để migration sang đích riêng và phục hồi.

Catalog có **297 slot**. Plugin có bốn catalog skill miễn phí, ba foundation skill và một runtime skill: **tám skill có nội dung**. **293 nội dung catalog trả phí** không được đóng gói. Metadata của slot không có nghĩa là nội dung tác giả đã được cài.

Cài gói nội dung thuộc quyền sử dụng của bạn bằng công cụ hiện hành:

```bash
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap skills install /path/to/skill-pack.zip
```

[Hướng dẫn core](docs/GUIDE-SDD-CORE.md) giải thích binding, tương thích và nguồn gốc. Nội dung bên ngoài không cấp quyền ghi workspace. Giữ thư mục skill của người dùng khi đổi phiên bản. Bài diễn tập upgrade từ chối store không tương thích và giữ nguyên dữ liệu; runtime không tự hạ schema hoặc ghi đè state cũ.

Đọc [SUPPORT-MATRIX.md](docs/SUPPORT-MATRIX.md), [CONTRIBUTING.md](CONTRIBUTING.md) và completion report trong source để biết giới hạn và bằng chứng. Bộ test public dùng dữ liệu tổng hợp, không cần provider key. Chưa đủ bằng chứng qualify semantic/style nếu thiếu nhãn độc lập và thực thi live.
