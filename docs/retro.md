# Retro — Đảo Đèn Lồng, bốn phase AI SDLC

## Kết quả và cách đánh giá

Phase1 biến PRD tổng quát thành game Đảo Bến và headless. Quyết định hiệu quả nhất là dùng một core JavaScript cho trình duyệt và Python/QuickJS: cùng input, cùng luật, không viết hai bản gameplay. Tag đầu lưu14 test, scenario và ảnh thật. Phần đồ họa chỉ dùng hình học thủ tục, không mất thời gian tìm asset hay đưa khác biệt vật lý vào bộ chấm.

Phase2 chuẩn hóa số và mở thành ba Đêm,43 test. Bản ticket dán lần đầu mất bảng số/màu. Hỏi lại giúp tránh tự đặt số sai và sửa toàn bộ sau đó. Các fixture nhỏ cho dash, rơi, bùa, Gió Lạc và pause phát hiện lỗi sớm. Kiểm tra GUI riêng chứng minh được campaign, retry và lưu cài đặt; headless không đủ để chứng minh những phần đó.

Phase3 thay luật cốt lõi. Dầu dùng số nguyên1/60; ADR ghi state đèn và pipeline, changelog giải thích assertion bị thay. Không sửa tag/bằng chứng cũ.70 test kiểm tra đủ đèn không thắng sớm, dầu tắt đúng tick, refill/relight ở tick cuối, death ưu tiên và floor bonus lấy dầu chưa tròn. Việc phân biệt thay đổi yêu cầu với regression giúp không tắt test âm thầm.

Phase4 giữ gameplay, thêm non-functional/release.77 test cùng15 scenario tiếp tục đạt. Benchmark thực tế đo cảnh200 Bóng+100 đom đóm bằng renderer dùng chung, camera chuẩn và rawframe timing; soak chạy10 Đêm bằng một Context trong một tiến trình, RSS thật. Leaderboard được xác minh qua server restart và CLI export. Đổi phím được thử bằng input thật, không chỉ nhìn giá trị cài đặt. Cỡ chữ, reduced flash, phụ đề và palette có browser assertions.

## Những lỗi đã gặp và cách phát hiện

- AI đặt test và môi trường sai: tempfile mode700 gây lỗi sandbox Windows, console không in được tiếng Việt. TestCLI và log chỉ rõ lỗi; chuyển file tạm vào artifacts và dùng thông báo console phù hợp.
- Đo hiệu năng sai bối cảnh: SwiftShader ở Phase1 chỉ khoảng6FPS. Giữ nguyên bằng chứng đó, sau đó đo GPU Intel thật thay vì đổi con số. Phase4 không dùng FPS gameplay thay cho benchmark chuẩn; đo riêng với capturevideo tắt.
- Fixture vô tình có tương tác: test tốc độ đi qua cầu nhặt Bùa Gió nên chạy nhanh hơn. Tách fixture để cô lập cơ chế. Test vùng an toàn30 cũng từng đặt wander đang tìm đèn khác; sửa scenario, không sửa luật để chiều expected sai.
- Lỗi biên tick: recoil thiếu một bước; input giữ khiến tick hồi sinh đi lệch origin. Thêm assertion2m/60tick và origin/vel0 để sửa và ngăn lặp.
- Test yếu có thể tạo niềm tin sai: chỉ kiểm tra state drain chưa chứng minh chọn đúng đèn hòa khoảng cách. Bổ sung event xác định L1 thực sự bị hút. Các case verifier cũng kiểm tra trạng thái cuối, không chỉ có tên event.
- Chữ lớn làm header chồng ở settings/leaderboard. Xem screenshot phát hiện được điều assertion màu/font không thấy; ẩn brand ở màn phụ và cho settings/menu cuộn.

## Harness nào hữu ích nhất

AGENTS.md giữ lệnh và invariant ngắn:60Hz, scenario không thưởng, thứ tự tick, source duy nhất. Skill verify-game chỉ dẫn cách thu bằng chứng và không chốt khi đỏ. tools/verify.py là cổng có exitcode thật; browser_check bổ sung UI mà unit không bao phủ. CI có ma trận macOS/Linux, nhưng cấu hình CI không được coi là một lần chạy thành công. Git tag, ADR và changelog giữ được phiên bản đúng của luật và evidence.

Vẽ theo lô ở Phase4 dùng cùng hình học/màu/quầng sáng trong gameplay và benchmark, giảm drawcall thay vì giảm chất lượng riêng trong cảnh đo. Rawframe timings cho phép tính lại avg,p1low,p95; peak_mem_mb=null được giải thích cho bản web, không lấy JS heap giả làm RSS.

## Token, chi phí và nếu làm lại

Phiên làm việc không cung cấp usage/billing, nên không thể nêu tổng token hoặc tiền chính xác. Để ước lượng có căn cứ, dùng kích thước văn bản mã/tài liệu do agent tạo, loại vendor/đề bài/evidence rồi chia4byte/token; phương pháp và số đo được lưu trong docs/proof/phase-4/token-estimate.json. Đây là proxy cho lượng artifact, không phải API token: không tính reasoning,input,tool output,retry hay cache. Chi phí tiền: chưa có dữ liệu tài khoản. Không biến proxy thành số tiêu thụ thật.

Đã tiết kiệm bằng core dùng chung, fixture gọn, đọc đúng file, không sinh hình ảnh, không tải asset nghệ thuật, chỉ chạy lại khi có thay đổi/lỗi cần kiểm tra. Nếu làm lại, sẽ lưu ticket đầy đủ ngay đầu, tách CLI/renderer rõ hơn sớm và thêm kiểm thử timer/state boundary trước phần mỹ thuật. Cần review người chơi về cảm giác/âm thanh; testẩn và kết quả trên máy chấm chỉ giảng viên mới xác nhận được. Video và các báo cáo là những lần chạy thật, không phải lời agent tự bảo đã chạy.
