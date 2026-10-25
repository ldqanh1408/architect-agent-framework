# Nhật ký thay đổi

Mọi thay đổi đáng chú ý của dự án được ghi lại tại đây.

Định dạng theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), và dự án
tuân thủ [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Repository có hai loại số phiên bản, mang ý nghĩa khác nhau:

- **Phiên bản phát hành** (`VERSION`, git tag, `pyproject.toml`,
  `plugins/architect-agent-framework/.claude-plugin/plugin.json`) đánh phiên bản cho toàn bộ repository;
- **Phiên bản catalog** (trường `version:` bên trong mỗi `SKILL.md`) đánh phiên
  bản cho các skill package, vốn đã tiến hóa từ trước khi repository được công bố.

`scripts/check_versions.py` thực thi cả hai quy tắc này trong CI.

🌐 **Ngôn ngữ**: [English](CHANGELOG.md) | **[Tiếng Việt](CHANGELOG.vi.md)**

## [2.0.0] - 2026-10-24

### Thêm mới
- **Hợp nhất SDD Core v2.0 & 16 Lệnh Điều hành Kiến trúc**: Hoàn thiện vòng đời đặc tả kiến trúc ISO/IEC/IEEE 42010 trên Claude Code, OpenAI Codex và DeepSeek Harness (`dsh`) với 16 slash commands, 8 bundled skills và 29 MCP tools.
- **Tự động Nhận diện Cấu hình Judge (`.env`) & Đánh giá Phân mảnh (`resolve_provider_config`)**: Tự động nạp `SDD_JUDGE_API_KEY`, `JEV_API_KEY`, `JEV_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` từ `.env` và hỗ trợ cả hai chuẩn `typesafe-jev` lẫn `openai-compatible`.
- **Công cụ Chia đợt Thực thi `sdd plan-waves` & Cờ `--out` Chuẩn UTF-8**: Sinh các wave lockfiles bất biến theo thứ tự phụ thuộc (`--batch-size 4`) và ghi trực tiếp UTF-8 không BOM chống lỗi mã hóa trên Windows PowerShell.
- **Bản đồ Kiến trúc C4 & Bàn làm việc Duyệt ký số (`:8767`)**: Tự động trích xuất tiêu đề `# H1`, hiển thị các Hệ thống Ngoại vi (`c2Externals`) ở mức C1/C2 và ký nghiệm thu bằng khóa phần cứng WebAuthn Passkey.

### Sửa lỗi
- Sửa lỗi lệch vị trí cắt mục khi có khối code trong `_audit_prose_substance` và hỗ trợ đoạn văn 1 dòng có từ 20 từ trở lên.
- Đồng bộ `depth_witnesses` cho cả các artifact sổ cái (`CONCERN-INV`) khi chạy `sdd prepare-check`.
- Loại bỏ hoàn toàn script POSIX `runtime.sh`, thống nhất 100% lệnh gọi qua `architect_runtime.py --bootstrap` đa nền tảng.

## [1.0.0] - 2026-10-12

Lần phát hành công khai đầu tiên của framework dưới dạng plugin Claude Code. Framework miễn
phí, giấy phép MIT. Cả 297 skill đi kèm dưới dạng **khe skill**: mỗi khe mang hợp đồng và
mẫu workspace, nên router, runtime nhiều agent và các gate biết đủ mọi skill. Ruột của một
khe miễn phí cho bốn skill (`architect-skill-orchestrator`, `adr-authoring`,
`agent-workflow-design`, `arch-review-task`) và cài riêng cho các skill còn lại. Plugin chạy
từ marketplace mà không cần clone: launcher dùng Python đã có gói của framework, hoặc `uv`
tải đúng phiên bản framework của plugin. Gói Python phát hành là `architect-agent-framework`
trên PyPI.

### Thay đổi — một plugin

- Hai plugin Claude Code (`plugins/claude-code`, `plugins/architect-runtime`) gộp
  thành một, `plugins/architect-agent-framework`: mười slash command, năm
  skill (bốn skill catalog miễn phí và `architect-runtime`), MCP server `architect-runtime` và hook hộp cát. Marketplace chỉ còn liệt
  kê plugin này; `plugins/claude-code/plugin.json` cũ đặt sai chỗ và không qua
  được `claude plugin validate`.
- `scripts/build_plugin_skills.py` giữ lại skill `architect-runtime` của plugin
  khi build lại, và `--check` nay báo lỗi cả khi skill bundle lệch catalog, không
  chỉ khi thiếu. Bundle đã được sinh lại.
- README và INSTALL mô tả đúng MCP server đang có (`runtime mcp`, mười sáu tool) thay
  cho module `adapters.mcp_server`. Các thư mục cũ `plugins/codex`, `plugins/agy` và
  `plugins/hermes` đã bị gỡ.

### Gỡ bỏ

- Công cụ của bản thương mại và các tệp nháp đã rời khỏi cây mã công khai.

294 file `SKILL.md` trong catalog đã được viết tay lại lên v2.1.0, nhưng toàn bộ
tooling xung quanh vẫn mô tả hình dạng sinh tự động cũ. Bản này hoà giải hai bên:
tooling khớp với nội dung, và nội dung được bảo vệ khỏi tooling.

### Đã sửa

- **Regenerate không còn phá catalog.** `export-skills` mặc định
  `--outdir exported_skills`, xoá từng package rồi dựng lại từ template v2.0.0 —
  chạy một lần là thay sạch 294 nội dung viết tay bằng text chung chung. Giờ
  generator coi `SKILL.md` và `references/research-basis.md` là nội dung viết tay
  và giữ nguyên qua mỗi lần regenerate; `--outdir` không còn giá trị mặc định; ghi
  vào thư mục đã có skill bắt buộc phải có `--force`. Cờ `--regenerate-skill-md`
  vẫn còn để chủ động reset một file khi thật sự muốn.
- **Regenerate không còn xoá file ở gốc catalog.** Quá trình sinh tráo nguyên cây
  mới vào, làm mất `exported_skills/agent.md` một cách âm thầm.
- **174/294 package fail chính validator của nó.** `check_skill_package.py` đòi
  heading `Common Pitfalls`, nhưng bản viết lại v2.1.0 đã thay bằng
  `Required Distinctions` ở 222 package — nên bước validate mà chính `SKILL.md`
  hướng dẫn lại exit 1. Gate giờ đòi *mục nội dung*, chấp nhận mọi tên heading mà
  catalog thực sự dùng.
- **CI đang đỏ trên `main`.** `package.yml` của mọi package và release manifest
  đều giữ hash cũ của `SKILL.md`; `release-check` fail cả 294. Manifest đã được
  sinh lại và giờ được kiểm tra thật.
- **`fail_closed: true` chỉ là trang trí.** `package.yml` ghi sha256 và số byte
  cho từng file nhưng không ai đọc. Giờ cả validator từng package lẫn gate cấp
  catalog đều verify.
- **`validate_catalog.py` báo catalog sạch trong khi 174 package hỏng.** Nó không
  kiểm heading lẫn hash manifest; giờ kiểm cả hai.
- **Khôi phục một file bị hỏng.** `architect-skill-orchestrator/SKILL.md` bị dán
  lẫn 20 dòng dấu diff (`+`), che mất mục `Verification Checklist`.
- **Ghim line ending.** Với `core.autocrlf=true` và không có `.gitattributes`,
  checkout ghi lại chính những file mà manifest hash, khiến `release-check` fail
  trên Windows nhưng vẫn xanh trên CI.

### Đã thay đổi

- **Plugin Claude Code giờ tự chứa.** Trước đây plugin có 5 slash command, không
  có skill nào, và các command lại gọi `python -m architect_framework...` — thứ
  mà người cài qua marketplace không hề có. Giờ plugin đóng gói bộ khung 11 skill
  (orchestrator + một domain architect chủ đạo mỗi cluster, ~2K token mô tả thay
  vì ~62K của cả catalog), và mọi command chạy được không cần package Python,
  chỉ dùng nó như đường tăng tốc tuỳ chọn.
- **Phần trích dẫn nghiên cứu rời khỏi `SKILL.md`.** Mục
  `Open-Source Research Basis` — 435 KB, khoảng 109K token trên toàn catalog —
  giải thích skill được thiết kế ra sao chứ không cần để chạy skill. Giờ nó nằm ở
  `references/research-basis.md`, load theo yêu cầu, và để lại một dòng trỏ đường.
  Nội dung chuyển nguyên văn; không tóm tắt, không cắt bỏ.
- **Quy tắc chung được ghi một lần** trong `exported_skills/agent.md` (khung
  blocking, khung resume, và nội dung nào nằm ở đâu) thay vì lặp lại rải rác.
- **Test suite chạy được trở lại.** 17 test mỗi cái đều sinh lại cả 294 package.
  Giờ catalog được sinh một lần mỗi phiên rồi dùng chung ở dạng read-only hoặc
  bản sao; chỉ những test thật sự kiểm hành vi sinh mới còn tự sinh.

### Đã thêm

- `scripts/build_plugin_skills.py` — dựng bộ skill đóng gói kèm plugin từ catalog,
  có `--check` gắn vào CI để bộ này không bị lệch.
- `scripts/extract_research_basis.py` — script migration idempotent đã chuyển các
  mục provenance.
- `tests/test_authored_content.py` — test hồi quy cho phần viết tay của catalog:
  giữ nội dung qua regenerate, guard `--force`, phát hiện manifest drift, và kiểm
  mục nội dung + hash cho từng package.

## Trước bản phát hành công khai (2026-08-01)

Bản phát hành công khai đầu tiên. Bộ skill và Python framework đã tồn tại từ
trước; bản này bổ sung mọi thứ cần thiết để sử dụng chúng từ bên ngoài
repository.

### Thêm mới

- **Installer** — `install.sh` (macOS, Linux, WSL, Git Bash) và `install.ps1`
  (Windows PowerShell). Cả hai làm phẳng catalog lúc cài, nhờ đó repository giữ
  được bố cục dễ đọc `domains/<NN_cluster>/<skill>` trong khi agent nhận được thư
  mục phẳng mà runtime yêu cầu. Hỗ trợ chọn theo skill, theo cluster, hoặc
  `--all`; nhắm tới Claude Code, Codex CLI, opencode và Cursor ở phạm vi người
  dùng hoặc dự án; kèm `--dry-run`, `--force` và `--uninstall` để việc cài đặt có
  thể hoàn tác.
- **Build phát hành** — `scripts/build_release.py` sinh ra cây phẳng sẵn sàng cài,
  `index.json` cho máy đọc, `INDEX.md` cho người đọc, một file zip cho mỗi cluster
  cộng một bundle đầy đủ, và `SHA256SUMS.txt`. Bundle theo cluster tồn tại để cài
  mười một skill bảo mật không phải tải về cả 294 skill.
- **Cổng kiểm tra catalog** — `scripts/validate_catalog.py` kiểm tra mọi package
  trong một lượt duyệt: thiếu file bắt buộc, frontmatter không parse được hoặc
  lệch tên, id trùng lặp sẽ đè lên nhau khi làm phẳng, và mô tả nằm ngoài khoảng
  kích hoạt ổn định. Báo cáo mọi vấn đề tìm thấy thay vì dừng ở lỗi đầu tiên.
- **Cổng kiểm tra phiên bản** — `scripts/check_versions.py` xác minh `VERSION`,
  `pyproject.toml`, `plugins/claude-code/plugin.json` và
  `.claude-plugin/marketplace.json` khớp nhau, và phiên bản catalog đồng nhất trên
  toàn bộ package.
- **Tích hợp liên tục** — `.github/workflows/ci.yml` chạy lint, bộ test trên
  Python 3.10 đến 3.13, hai cổng kiểm tra catalog và phiên bản, kiểm tra toàn vẹn
  release manifest, build bundle kèm xác minh cấu trúc, và smoke test installer
  trên Linux, macOS, Windows.
- **Tự động hóa phát hành** — `.github/workflows/release.yml` phát hành từ tag
  `v*`. Nó từ chối phát hành khi tag lệch với `VERSION`, chạy lại mọi cổng kiểm
  tra, build bundle và bản phân phối Python, trích release note từ file changelog
  này, rồi đính kèm artifact cùng checksum.
- **Manifest marketplace cho Claude Code** — `.claude-plugin/marketplace.json`, để
  cài plugin bằng `/plugin marketplace add`.
- **Tài liệu phát hành** — `INSTALL.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` và
  file changelog này, mỗi file đều có bản tiếng Việt tương ứng.
- **`VERSION`** làm nguồn chân lý duy nhất cho phiên bản phát hành.

### Sửa lỗi

- Một khối code fence bị hỏng trong `README.md` và `README.vi.md` khiến ví dụ
  Python SDK thứ hai hiển thị như văn bản thường thay vì như code.

### Ghi chú

Catalog gồm 294 skill package: 110 domain skill thuộc 10 cluster kiến trúc, 183
task skill thuộc 20 nhóm tác vụ, và 1 orchestrator. Mỗi package đều có `SKILL.md`,
một machine contract, references, scripts, assets, evaluations và agent manifest.
Tính toàn vẹn của catalog được ghim bằng `exported_skills/release-manifest.yml`,
kèm SBOM (`sbom.cdx.json`) và provenance in-toto (`provenance.intoto.jsonl`).

[Chưa phát hành]: https://github.com/ldqanh1408/Architect-Agent-Framework/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ldqanh1408/Architect-Agent-Framework/releases/tag/v1.0.0
