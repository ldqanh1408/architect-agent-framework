# Chính sách bảo mật

🌐 **Ngôn ngữ**: [English](SECURITY.md) | **[Tiếng Việt](SECURITY.vi.md)**

## Phiên bản được hỗ trợ

| Phiên bản | Được hỗ trợ |
| --- | --- |
| 1.0.x | Có |
| < 1.0 | Không — bản tiền phát hành, hãy nâng cấp lên 1.0.x |

Bản vá bảo mật được phát hành trên minor mới nhất. Các minor cũ không được
backport trong giai đoạn 1.x.

## Báo cáo lỗ hổng

Hãy báo cáo riêng tư, không qua issue công khai.

1. Ưu tiên: mở một
   [security advisory riêng tư](https://github.com/ldqanh1408/Architect-Agent-Framework/security/advisories/new)
   trên repository này.
2. Nếu bạn không dùng được cách trên, hãy liên hệ maintainer qua trang GitHub cá
   nhân của họ và xin một kênh riêng tư trước khi chia sẻ chi tiết.

Vui lòng nêu rõ:

- vấn đề là gì và nằm ở đâu trong repository;
- các bước hoặc input cần thiết để tái hiện;
- kẻ tấn công đạt được gì — đây là yếu tố quyết định mức nghiêm trọng;
- phiên bản hoặc commit bạn đã kiểm thử;
- proof-of-concept nếu có, ghi rõ đó là PoC.

**Cam kết thời gian phản hồi.** Xác nhận đã nhận trong 5 ngày làm việc, đánh giá
sơ bộ trong 10 ngày, và bản vá hoặc lý do không vá được ghi rõ trong 90 ngày với
các vấn đề đã xác nhận. Đây là dự án do tình nguyện viên duy trì; nếu trễ hạn,
bạn sẽ được thông báo thay vì bị bỏ mặc.

**Công bố.** Vui lòng chờ 90 ngày kể từ lúc được xác nhận trước khi công bố công
khai, hoặc sớm hơn nếu hai bên thống nhất sau khi bản vá được phát hành. Người báo
cáo được ghi nhận trong advisory và changelog, trừ khi họ không muốn.

## Mô hình mối đe dọa thực tế của dự án này

Điều này quan trọng hơn so với một thư viện thông thường, vì phần lớn repository
không phải mã thực thi — đó là các chỉ dẫn mà AI agent đọc và hành động theo.

### Nội dung skill là input không đáng tin đối với một tiến trình đáng tin

Một skill package là văn bản mà agent nạp vào context của chính nó rồi làm theo.
Một skill hướng dẫn agent rò rỉ file, làm suy yếu một biện pháp bảo mật, hoặc chạy
lệnh ngoài dự kiến là một lỗ hổng thật sự, dù nó không chứa dòng code nào.
**Hãy báo cáo nội dung skill độc hại hoặc mang tính thao túng như một vấn đề bảo
mật**, không phải như một lỗi tài liệu.

Catalog được viết theo một kỷ luật cố định nhằm giới hạn nhóm vấn đề này: mỗi
skill khai báo một cây thư mục output mà nó sở hữu, bắt buộc coi mọi thứ bên ngoài
là chỉ đọc, và phải phân loại các khẳng định theo bằng chứng thay vì tự khẳng
định. Một skill âm thầm nới rộng phạm vi ghi của chính nó, tự bịa ra thẩm quyền
không được cấp, hoặc ghi ra ngoài cây thư mục của nó là một khiếm khuyết đáng báo
cáo.

### Việc cài đặt ghi vào cấu hình agent của bạn

`install.sh` và `install.ps1` copy thư mục vào `~/.claude/skills` và các vị trí
tương đương. Bất kỳ điều gì khiến các script này ghi ra ngoài thư mục đích đã giải
quyết — một skill id được dựng đặc biệt, một tên thư mục path-traversal, một
symlink trong catalog — đều là lỗ hổng. Dùng `--dry-run` để kiểm tra kế hoạch
trước.

Cả hai script đều ghi một file đánh dấu `.architect-agent-framework` vào mỗi
package được cài và từ chối `--uninstall` một thư mục không có file đó, chính là để
việc gỡ cài đặt không thể bị biến thành lệnh xóa các file không liên quan.

### Các validator là biện pháp kiểm soát chuỗi cung ứng, không phải thủ tục hình thức

`exported_skills/release-manifest.yml` ghim SHA-256 cho từng file trong catalog;
`sbom.cdx.json` và `provenance.intoto.jsonl` ghi lại release chứa những gì và được
tạo ra như thế nào. Bất kỳ cách nào khiến `release-check` vẫn pass với nội dung
không khớp manifest đều triệt tiêu ý nghĩa của việc công bố hash, và là một vấn đề
bảo mật.

Xác minh bundle đã tải trước khi giải nén:

```bash
sha256sum -c SHA256SUMS.txt --ignore-missing
```

### Ngoài phạm vi

- Lời khuyên kiến trúc mà bạn không đồng tình, hoặc một skill đưa ra thiết kế bạn
  cho là sai. Đó là vấn đề về tính đúng đắn — vui lòng mở issue thông thường.
- Lỗ hổng trong một hệ thống mà agent đã thiết kế khi dùng các skill này. Skill
  tạo ra tài liệu; chúng không xây dựng hay vận hành hệ thống.
- Bất kỳ điều gì đòi hỏi kẻ tấn công đã kiểm soát được máy của bạn hoặc thư mục
  cấu hình của agent.
- Denial of service do cài cùng lúc cả 294 skill. Đây là hành vi đã được ghi rõ
  kèm cách khắc phục đã được ghi rõ: cài ít skill hơn.

## Khuyến nghị tăng cường cho người vận hành

- Chỉ cài cluster bạn cần. Mô tả của mọi skill đã cài đều đi vào context của model,
  và bề mặt nhỏ hơn thì vừa an toàn hơn vừa đáng tin cậy hơn.
- Ghim theo tag thay vì bám `main`, và xác minh checksum khi tải về.
- Chạy agent với phạm vi workspace đúng với công việc. Skill tự khai báo ranh giới
  ghi của nó, nhưng sandbox của agent mới là thứ thực thi ranh giới đó.
- Đọc `SKILL.md` trước khi cài skill từ bất kỳ bản fork nào của repository này.
  Chính sách này không áp dụng cho các bản fork.
