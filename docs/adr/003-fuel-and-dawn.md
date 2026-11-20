# ADR-003 — Đèn có nhiên liệu, chiến thắng tại bình minh

Trạng thái: áp dụng cho Phase3; nguồn Ticket-03 / contract1.2.

## Bối cảnh

Phase2 coi đèn sáng là trạng thái vĩnh viễn và kết thúc sớm khi đủ đèn. Ticket mới làm cả hai giả định mất hiệu lực. Thêm logic riêng cho renderer sẽ làm headless và game lệch nhau; mọi luật tiếp tục ở `src/core.js`.

## Quyết định

Mỗi đèn giữ `lit`, `deposited`, `fuelUnits`, `ever_lit`, `relit_count`. Một fuelUnits bằng1/60 dầu: tối đa6000, tự hao1 mỗi tick, mỗi Bóng hút5 mỗi tick, mỗi đom đóm thêm600. Tất cả phép so ngưỡng/bù dầu và floor bonus dùng số nguyên gốc; chỉ snapshot/event làm tròn dầu1chữ số. JSON có thể viết100 thay100.0 vì chúng cùng một giá trị số.

Chuyển trạng thái:

- Chưa sáng: nạp đủ10 → sáng/fuel6000, ever_lit=true, thưởng100 và tăng successful_lights.
- Tắt nhưng ever_lit: nạp đủ5 → sáng/fuel6000, tăng relit_count, thưởng40 và tăng successful_lights.
- Sáng: châm dầu theo ceil lượng còn thiếu; chạm trần6000. Không có chỗ nhận thì bị loại khỏi danh sách tương tác.
- Đang sáng mà fuelUnits≤0: tắt, deposited0, giữ ever_lit, phát lantern_out. Không tự xóa dấu vết từng sáng.

Bước timer sau pause xử lý dầu của tất cả đèn và các Bóng đã đang drain. Tổng hợp các Bóng trước khi tắt đèn để không phụ thuộc thứ tự mảng. fuel_drain ghi mỗi60 bước hút thực sự liên tiếp của từng Bóng; pause giữ cả đếm này. Nếu ngừng hút thì đếm lại từ0. Bóng mới vào drain ở bước actor bắt đầu hút từ tick sau. Sau refuel đủ ngưỡng, bước safe-zone hủy drain và đẩy ra biên; threshold dùng fuelUnits1800, không dùng fuel đã làm tròn.

Một hệ quả có chủ đích của thứ tự bắt buộc: đèn có100 dầu ở snapshot tick0 còn99.983… tại tương tác tick1, nên có thể nhận1 đom đóm. Test đầy tuyệt đối gọi riêng thao tác interaction trước tick; test headless khác xác nhận decay diễn ra trước refill. Không thêm vùng chết quanh100 vì sẽ trái công thức ceil.

Chỉ wander tìm đèn yếu; chase vẫn theo Mây. Drain dùng ngưỡng phát hiện6m riêng, không bị quy tắc wander12m ghi đè khi vẫn hút. Khi hết choáng, snapshot của bước chuyển ghi wander trước khi chọn mục tiêu ở bước kế tiếp; pulse mới trong cùng tick vẫn được chốt/đẩy bình thường.

Không còn nhánh all_lit trong kết quả. Mỗi tick xét: hết lửa→no_flames; nếu thời gian hết mới xét ceil(win_ratio*lampCount). Khi thắng chỉ cộng bonus đèn đang sáng và lửa; floor(fuel) lấy dầu chưa làm tròn. Kết quả tính sau extinction, refill, pulse, hit và spawn của tick cuối. Nhờ vậy thắp lại ở tick cuối có thể cứu bình minh nhưng chết ở tick cuối luôn thua.

Sức chứa suy ra từ số lần thắp thành công, không từ đếm đèn hiện sáng/ever_lit. Constructor chỉ nạp trạng thái scenario, không tăng bộ đếm hay điểm. Renderer đọc capacity từ cùng model; setting mù màu lưu trình duyệt và không chạm core/output headless.

## Hệ quả và kiểm chứng

Contract tăng1.2; các consumer cũ cần đọc fuel/capacity/drain, không chờ early-win. Các tag/bằng chứng cũ giữ nguyên. Danh sách test thay thế nằm trong CHANGELOG.md; không skip lớp Phase2 khi version khác1.1 nữa. Case nhiên liệu ở tests/scenarios/fuel.json; unit tests kiểm tra cả dầu nội bộ chưa tròn, threshold, tick cuối, tổng nhiều Bóng và scenario không thưởng. Browser QA kiểm tra thanh dầu/blink, hình đèn tắt và màu/settings qua reload.
