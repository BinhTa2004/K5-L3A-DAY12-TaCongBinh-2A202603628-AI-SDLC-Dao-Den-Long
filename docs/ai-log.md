# Nhật ký làm việc với AI

## Phase 1

- Người điều phối: Tạ Công Bình; công cụ: Codex.
- Đầu vào: đọc toàn bộ tài liệu repo, PRD-0 và Test Contract do người dùng cung cấp.
- Quyết định: browser Three.js + core JS thuần; Python/QuickJS chạy nguyên core ở headless. Không viết hai bản luật game.
- Harness: AGENTS.md, skill verify-game, tools/verify.py trả mã lỗi khi regression đỏ, CI macOS/Linux.
- Kiểm chứng: test đơn vị/scenario, tính tất định, chạy đủ Đêm, Chrome headless và ảnh thực tế. Các báo cáo được sinh bằng lệnh, không sửa tay.
- Lỗi AI/môi trường đã phát hiện: test dùng thư mục tạm mode 700 gây PermissionError trong sandbox Windows; đổi thành file riêng trong artifacts. Console Windows không in được tiếng Việt; thông báo server đổi sang ASCII.
- Token/chi phí: giao diện phiên này không cung cấp số đo chính xác; chưa có số liệu, không bịa số. Tiết kiệm bằng dùng chung core, test CLI gọn, không sinh ảnh hay tải asset nghệ thuật.

## Retro Phase 1

Tách logic khỏi renderer cho phép kiểm tra sớm input/tick và tái lập output. Tài liệu Phase 2 được dán lần đầu thiếu bảng; đã hỏi lại và nhận đủ thay vì tự đoán chuẩn. Ưu tiên tiếp: chuẩn hóa, thêm scenario cho từng cơ chế, kiểm tra lại UI và số đo thực tế.

## Phase 2

- Đã nhận bảng chuẩn từ người dùng; giữ tag Phase1 với tuning cũ, đổi bản hiện tại sang contract1.1.
- Tuning chuẩn, ba bản đồ, dash, jump pads, terrain/ramp/tower, pulse3D, recoil, rơi/hồi sinh, Gió Lạc, Bùa Gió, gió định kỳ, pause và snapshot mới dùng chung core.
- GUI: chiến dịch ba Đêm, Bình Minh và tổng điểm Đêm thắng; thua retry; menu pause; localStorage cài đặt; nhạc/cue tổng hợp; HUD, cảnh báo lá/gió, bảng màu.
- Harness được cập nhật thật trong AGENTS.md và skill verify-game; verifier kiểm tra cả event và trạng thái cuối của feature scenario. Browser QA riêng vì headless không chứng minh được giao diện.
- Kiểm chứng:43 test gồm14 regression Phase1;8 feature scenario lưu JSONL; đủ3 Đêm, output lặp byte-identical; parity browser/QuickJS; GUI movement/pause/campaign/retry/settings; FPS từng bản đồ có đủ số Bóng tối đa. Đo trên Windows10, Python3.12.9, Intel HD630/D3D11; xem báo cáo sinh tự động để lấy số chính xác.
- Lỗi/phát hiện: (1) đo WebGL bằng SwiftShader chỉ6FPS, đổi sang GPU mặc định cho số đo thực tế≈60FPS; giữ bằng chứng software trong Phase1, không sửa lại. (2) test tốc độ qua cầu vô tình nhặt Bùa Gió; tách scenario không bùa để đo chạy thường. (3) rà tick phát hiện recoil chỉ đi59 bước; sửa đủ60 và thêm test quan sát2m. (4) chuẩn hóa chữ UI và bổ sung lõi đèn đúng palette. (5) test rơi được mở rộng với phím di chuyển đang giữ: tick hồi sinh phải origin/vel0, không được đi ngay trong tick đó; đã sửa và chạy regression.
- Chưa có quyền truy cập test ẩn; chưa chạy trên máy chấm macOS/Linux. CI đã cấu hình nhưng chỉ coi là bằng chứng khi dịch vụ chạy thành công. Chất lượng nghe âm thanh và review độc lập cần người dùng kiểm tra khi chơi.

## Ước lượng token/chi phí

Không có bảng usage/billing của phiên này. Không thể báo tổng token thật, cache hay chi phí. Một phép đo tham khảo cho quy mô đầu ra: mã/tài liệu do agent tạo ở Phase1 khoảng69.767 byte, tương đương khoảng17.442 token theo quy tắc thô4byte/token; mã hiện tại khoảng100.861byte (~25.215token). Đây **chỉ là proxy kích thước mã**, không phải tổng token model đã tiêu thụ, không tính reasoning, input, retry, tool output hay cache; văn bản tiếng Việt cũng không tuân tỷ lệ này chính xác. Chi phí: chưa có dữ liệu từ tài khoản người dùng.

## Retro cuối Phase 2

Hiệu quả nhất: cùng một core cho game/headless; các case nhỏ bắt lỗi thứ tự tick trước khi làm GUI; bằng chứng có lệnh tái lập và hash; hỏi lại bảng bị mất thay vì tự điền chuẩn. Các tính năng hiển thị cần browser QA riêng, đo FPS bằng thời gian requestAnimationFrame thật. Nếu làm lại: lưu bảng đầy đủ ngay lúc nhận, tách fixture ngay từ đầu, thêm sớm các test biên timer/recoil để giảm vòng sửa. Phần sáng tạo chỉ là mô hình/quầng sáng/nhạc thủ tục, không thêm thực thể ảnh hưởng headless.

## Phase3 — Change Request Đèn cạn dầu

- Nguồn Ticket-03 do người dùng gửi; contract1.2 thay luật đèn vĩnh viễn, thắng sớm, capacity cố định và điểm. Quyết định lưu tại ADR-003; CHANGELOG chỉ rõ4 nhóm assertion cũ thay và decorator skip được xóa. Mọi regression còn hiệu lực tiếp tục chạy.
- Đổi trạng thái đèn thành fuelUnits/ever_lit/relit_count; dùng đơn vị nguyên1/60. Dầu/drain ở bước timer trước interaction; ngưỡng30 và floor bonus dùng dầu gốc. Chỉ kiểm tra thắng tại bình minh sau extinction/refill/hit.
- Thêm drain và chọn đèn yếu cho wander, thoát drain đúng điều kiện; sức chứa theo số lần thắp thật; palette lưu riêng renderer. Harness AGENTS/skill/verifier được cập nhật trong git.
- Phát hiện khi kiểm chứng: test ngưỡng30 ban đầu đặt wander nhưng đèn ở đúng30 không phải mục tiêu yếu, nên Bóng đi về đèn tắt khác. Sửa scenario thành chase hướng Mây để cô lập kiểm tra chặn ở vùng an toàn. Không sửa luật để chiều theo expected sai.
- Biên ceil quan trọng:100 dầu ở tick0 sẽ hao trước E ở tick1, nên có thể nhận1 đom đóm. Ghi rõ ADR và có cả test exact-full trước tick lẫn test pipeline đầy đủ; không tự thêm epsilon bỏ hao.
- Thêm kiểm tra hết choáng phải xuất hiện trạng thái wander ở bước hồi phục trước lần chọn tiếp; kiểm tra tie theo event đèn thực sự bị hút, không chỉ kiểm tra tên trạng thái.
- Bằng chứng: unit/regression +15case JSONL, toàn Đêm tất định; browser kiểm tra byte parity, campaign/retry/total, thanh dầu/blink/capacity, màu mắt/viền và reload setting, FPS từng Đêm. Scenario QA thắng nhanh được đánh dấu rõ trong spec; không giả làm video chơi cả Đêm.
- Token/chi phí Phase3: không có API usage/billing; không báo con số tiêu thụ thật. Ước lượng chỉ dựa kích thước mã thay đổi (xem git diff/commit), không gồm reasoning/input/cache/tool; chi phí chưa có số liệu. Dùng chung core và chạy case nhỏ trước GUI để giảm vòng thử.
- Retro: state và timer phải có test tại đúng tick chuyển. Chọn model số nguyên ngay từ đầu tránh lỗi ngưỡng; giữ ADR/test migration cạnh code giúp phân biệt hồi quy thật với luật đã bị thay. Cần người dùng chơi thử để review cảm giác và nghe âm thanh; test ẩn vẫn chưa truy cập.
