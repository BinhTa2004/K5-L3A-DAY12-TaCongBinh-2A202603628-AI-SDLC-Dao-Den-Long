# Spec và quyết định — Phase 1

Nguồn: `requirements/phase-1.txt`, Test Contract v1.0. Không suy diễn ticket chưa phát hành.

| Yêu cầu | Tiêu chí nghiệm thu | Kiểm chứng |
|---|---|---|
| Màn 3D, Mây đội nón treo đèn | Chơi từ menu; WASD, nhảy, camera; nhân vật có nón và đèn | Screenshot và browser_check |
| Năm đèn, nhặt/nạp ánh sáng | Nhặt tới sức chứa; E nạp một đèn, ghi nhớ tiến độ | PhaseOne pickup/deposit/winning |
| Bóng Mực đuổi, gây hit | Tiếp cận mất 1 lửa; bất tử ngăn hit lặp | PhaseOne damage |
| Tỏa sáng | Tốn 3, choáng và đẩy mục tiêu; giữ nút không lặp | PhaseOne pulse |
| Thắng/thua/điểm/chơi lại | Đủ năm đèn thắng, hết lửa/hết giờ thua; nút chơi lại | Unit + browser |
| Contract | Tick 0 trước input, 60 Hz, JSONL end; input lỗi mã 2 | tests/test_contract.py |
| Determinism | Cùng seed và đầu vào cho byte output giống nhau | verify.py |

Giả định Phase 1: đảo phẳng bán kính 40 m; số liệu tùy chọn nằm duy nhất trong game.contract.json; nhảy 8 m/s, trọng lực 20; input đổi vận tốc ngay; không va chạm cây trang trí. Điểm được cộng khi nạp, không khi nhặt. Thứ tự kết thúc: hết lửa, đủ đèn, hết giờ. Tỏa sáng dùng khoảng cách XZ ở v1.0. Mỗi lần E chọn đèn chưa sáng gần nhất, hòa chọn id theo thứ tự chuỗi. Đom đóm rơi có TTL 900 tick ở v1.0. Dựng scenario không cộng điểm hay phát event.

Tình trạng: xem report sinh tự động; không suy ra đã đạt test ẩn. Chưa có kết quả chạy trên máy chấm macOS/Linux; CI chỉ là cấu hình tới khi chạy thật.
