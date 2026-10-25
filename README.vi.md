# Architect Agent Framework

Bản bàn giao: **2.0.0**. Trạng thái phát hành: **RELEASE_CANDIDATE**.

Bộ công cụ và Runtime điều phối đa tác tử thiết kế kiến trúc phần mềm chuẩn quốc tế (ISO/IEC/IEEE 42010 · C4 Model · arc42 · DDD · ASD-STE100 Advisory) hỗ trợ trực tiếp **Claude Code (`claude`)**, **OpenAI Codex (`codex`)**, và **DeepSeek Harness (`dsh`)** trên Windows PowerShell, macOS và Linux.

## Bắt đầu nhanh trong 60 giây (Zero System Prompt)

```bash
uv sync --locked --all-extras
npm ci --ignore-scripts
npm run build:console

# Cài đặt trọn bộ Core Skills, Catalog Skills và 16 Commands cho cả Claude, Codex và DeepSeek Harness:
.\install.ps1 -All -Agent all        # Windows PowerShell
./install.sh --all --agent all        # macOS / Linux / WSL
```

Cấu hình `.env` (tại thư mục dự án hoặc `~/.architect-framework/.env`) khi cần chấm điểm JEV trực tuyến (`--live`):

```dotenv
JEV_API_KEY=jev_live_xxxxxxxxxxxxxxxx
JEV_KEY=jev_live_xxxxxxxxxxxxxxxx
ARCHITECT_ALLOW_BASE=1
```

## 8 Tình huống Sử dụng Chuẩn (`UC-01` .. `UC-08`)

| Mã UC | Lệnh kích hoạt | Profile & Chế độ mặc định | Kết quả đầu ra |
|---|---|---|---|
| **UC-01: Làm rõ yêu cầu từ ý tưởng thô** | `/architect-clarify <ý tưởng hoặc brief.md>` | `seed` · `solo-author` | Phỏng vấn Socratic (tối đa 5 câu hỏi có phương án mặc định) -> `clarified-requirements.md` |
| **UC-02: Thiết kế nhanh MVP (5–10 phút)** | `/architect-quickstart [nguồn]` | `standard` · `solo-author` | Khởi tạo và viết hoàn chỉnh 12–25 tài liệu cốt lõi, tự chạy `prepare-check` và `sdd check` PASS |
| **UC-03: Thiết kế Maximal cấp Doanh nghiệp** | `/architect-design --profile maximal --sources <...> --out <dir>` | `maximal` · `solo-author` | Tự động thực thi trọn vẹn 6 Phases (Intake -> Materialize -> Waves -> Prepare-Check -> Gate -> Review) |
| **UC-04: Kiểm toán Codebase & Nghiệm thu** | `/architect-audit <code/test> --against <SRS>` | `standard` / `maximal` | Đối soát code/test thực tế với SRS/ADR, ghi nhận xung đột `CNF-*` và kế hoạch khắc phục |
| **UC-05: Giải quyết 1 bài toán lẻ (ADR/API)** | `/architect-route` & `/architect-execute --standalone` | `standalone` | Định tuyến tới cặp Domain × Task skill và xuất ngay tài liệu `.md` độc lập |
| **UC-06: Kiểm tra Gate & Phản biện độc lập** | `/architect-check --full` & `/architect-review [--live]` | Theo workspace | Kiểm tra chống stub (`DTG-01..10`), chạy `02-spec-critic` và chấm điểm JEV theo shard `< 75 KB` |
| **UC-07: Quản lý thay đổi yêu cầu (CR)** | `/architect-change <nội dung thay đổi>` | Incremental | Phân tích vùng ảnh hưởng trên đồ thị và bảo toàn `canonical_facts` / `guards` (`DTG-07`) |
| **UC-08: Bản đồ C4, Skill Packs & Passkey** | `/architect-console`, `/architect-skills`, `/architect-approve` | Web Console (`:8767`) | Khám phá bản đồ C4 (`< 20ms`), quản lý 297 skill slots và ký duyệt WebAuthn Passkey |

Xem hướng dẫn chi tiết toàn bộ 16 Commands và cách cấu hình từng Harness tại [docs/QUICKSTART-USE-CASES.md](docs/QUICKSTART-USE-CASES.md) và [INSTALL.vi.md](INSTALL.vi.md).
