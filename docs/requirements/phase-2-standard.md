# Ticket-02 — phần bảng bị mất khi dán lần đầu

Nguồn: người dùng bổ sung nguyên nội dung Ticket-02 trong phiên làm việc. Đọc cùng `phase-2.txt` (bản đồ, tính năng, contract). Các bảng sau thay toàn bộ tuning tự chọn Phase 1.

| Nhóm | Chuẩn bắt buộc |
|---|---|
| Chạy | 6 m/s; tăng tốc/dừng ≤0.1s; điều khiển trên không đầy đủ |
| Nhảy | 7 m/s; trọng lực −20 m/s²; chỉ khi chạm đất |
| Lướt | 14 m/s; 12 tick; hồi 90 tick từ lúc bắt đầu; hướng di chuyển hoặc hướng mặt; trên không giữ độ cao; không bất tử |
| Nhặt | Sức chứa 10; XZ ≤1m, chênh cao ≤1.5m |
| Sinh đom đóm | Ban đầu 20 điểm khác nhau; trần 30; thêm 1 ở điểm trống tại tick 240,480,…; hết điểm bỏ lượt |
| Đèn | 10 đom đóm; nạp nhiều lần; E trong 2m; chọn đèn chưa sáng gần nhất, hòa chọn id nhỏ hơn |
| An toàn | Đèn sáng: bán kính 6m; Bóng ở trong bị đẩy ra trong tối đa 30 tick và không gây damage lúc đó |
| Pulse | Tốn 3; bán kính 3D 5m từ chân Mây +0.8m; hồi 180 tick; chốt mục tiêu ngay khi kích hoạt |
| Hiệu ứng pulse | Choáng 120 tick; đẩy ngang 4m trong 15 tick đầu; dừng ở vật cản; trùng vị trí đẩy +X; pulse lại làm mới; không giết |
| Bóng Mực | 4m/s, Đêm 3:4.5m/s; phát hiện12m, bỏ đuổi18m; chạm XZ≤1m và cao≤1.5m |
| Hit | Tối đa1 lần/tick; Bóng gây hit recoil2m/60tick; bất tử ngăn hit và recoil |
| Spawn Bóng | 2 tại tick300, rồi 1 mỗi khoảng sinh; điểm cách người≥15m; không có điểm hợp lệ thì bỏ; id S1,S2,… |
| Hậu quả hit | −1 lửa; rơi floor(carried/2) ở vành1.5–2.5m, TTL480tick, nhặt từ tick sau; bất tử90tick |
| Rơi | Y<−10, bỏ qua bất tử: −1lửa, mất toàn bộ carried; chờ60tick không nhặt/không bị chạm; hồi sinh origin, vel0, bất tử90tick; chết không hồi sinh |
| Lửa/thời gian | 3lửa, hồi đầy đầu Đêm; Đêm1/2/3:300/330/360s |
| Kết thúc | Hết lửa→no_flames trước; còn sống đủ đèn→won kể cả tick hết giờ; còn lại hết giờ→dawn |
| Điểm | +10/đom đóm nạp; +100/đèn; +5/Bóng trúng pulse mỗi lần; thắng thêm floor(time_left)*2+flames*50; tổng chỉ cộng Đêm đã thắng |

| Thành phần | Hex chuẩn |
|---|---|
| Trời/sương | #0E1430 / #1B2350 |
| Cỏ/cát/gỗ/biển mây | #2F5D50 / #C9B48A / #6B4A2F / #12384A |
| Đèn sáng/lõi/tắt | #FFB347 / #FFE9B0 / #5B5F6E |
| Đom đóm lõi/quầng | #FFF6C2 / #FFE58A |
| Bóng thân/viền/choáng | #120A1A / #7A3CFF / #3A3450 |
| Áo/khăn Mây, bùa | #E8E2D0 / #C8102E |
| Viền vàng, điểm/Gió Lạc | #F2C14E / #8FA3B8 |
| UI nguy hiểm/chữ | #FF5A5F / #F5F1E6 |

Sai lệch màu cho phép tối đa 10% mỗi kênh; code dùng đúng mã màu cơ sở. Cường độ AmbientLight = `0.15 + 0.55 * lit / total`.
