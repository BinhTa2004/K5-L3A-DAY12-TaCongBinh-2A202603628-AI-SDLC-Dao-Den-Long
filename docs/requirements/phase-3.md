# Ticket-03 — Đèn cạn dầu / Contract v1.2

Nguồn: nội dung Change Request Phase3 do người dùng cung cấp trong phiên làm việc. Những luật không bị thay thế của Ticket-02 tiếp tục có hiệu lực. Tag bàn giao: `phase-3`.

## Thay đổi bắt buộc

- Fuel tối đa100, mới thắp hoặc thắp lại nhận100. Mỗi tick đèn sáng hao1/60. Hết dầu tắt, deposited0, ever_lit=true, phát lantern_out.
- E ở đèn sáng: used=min(carried,ceil((100−fuel)/10)); mỗi đom đóm thêm10, không vượt100. Full/used0 không được chọn, không event/điểm. Trong các đèn nhận được, chọn gần nhất, hòa id nhỏ hơn.
- Đèn chưa từng sáng cần10; đã từng sáng chỉ cần5. Thanh dầu trên đèn; fuel<30 thì đèn và thanh nhấp nháy1Hz.
- Đèn fuel<30 mất vùng an toàn; đúng30 vẫn có. Chỉ wander tìm đèn sáng yếu gần nhất, hòa id; không có thì tìm đèn tắt gần nhất. Chase không đổi mục tiêu.
- Wander tới đèn yếu trongXZ≤2 chuyển drain, đứng yên hút5/60 mỗi tick; nhiều Bóng cộng dồn với hao tự nhiên1/60.
- Drain→chase khi Mây trong6m; →stunned khi pulse; →wander khi đèn tắt, fuel≥30 hoặc cách đèn>2m. Hết choáng vềwander. Châm lên≥30 đẩy Bóng trong6m ra biên trong≤30tick, không gây damage lúc bị đẩy.
- Đêm1/2/3=240/270/300s. Không thắng sớm. Tại bình minh: còn sống và đèn đang sáng≥ceil(0.6*n) thì thắng:3/5,4/6,5/7. Death luôn ưu tiên, kể cả tick cuối. Reason: dawn_survived / dawn / no_flames, bỏall_lit.
- Tại bước2 trừ dầu tự nhiên+hút; ngay sau bước2 tắt đèn cạn. Xét kết quả sau tất cả cập nhật còn lại của tick.
- Capacity=min(20,10+2*successful_lights). Mỗi lần thắp/thắp lại thành công tăng bộ đếm; prelit scenario không tính. Reset mỗi Đêm; HUD cập nhật sức chứa.
- Điểm:5/đom đóm nạp (kể cả refuel),100/thắp đầu,40/thắp lại,5/pulse Bóng thường hoặc tổng15/Bóng đang drain. Khi thắng: mỗi đèn đang sáng được50+floor(fuel), mỗi lửa50. Bỏ thưởng thời gian. Tổng chiến dịch/retry giữ luật Phase2.
- Cài đặt lưu "Bảng màu dễ phân biệt": viền/mắt Bóng từ#7A3CFF sang#00B3FF, warning UI từ#FF5A5F sang#FFFFFF kèm⚠. Không chỉ dựa vào màu: đèn tắt xẹp20%, giấy rách; dầu yếu nhấp nháy.

## Contract1.2

Tuning thêm fuel_max100, fuel_decay_per_s1, fuel_per_mote10, relight_cost5, win_ratio0.6, drain_per_s5, low_fuel_threshold30, capacity_max20. Đổi ba duration như trên.

Snapshot đèn thêm fuel (làm tròn1chữ số, tắt=0), ever_lit, relit_count. Player thêmcapacity. Shade thêm trạng thái drain.

Scenario đèn nhận lit/fuel/ever_lit (lit:true thiếufuel→100), player nhậnsuccessful_lights, shades nhậntarget_lantern_id. Scenario không phát thưởng.

Event mới:

| Tên | data |
|---|---|
| refuel | lantern_id, amount, fuel |
| lantern_out | lantern_id |
| fuel_drain | lantern_id, shade_id, fuel; mỗi60tick đang hút |
| lantern_lit | thêm relight:boolean |
| game_over | reason thêm dawn_survived, bỏall_lit |

DoD: bằng chứng thật; ADR về trạng thái đèn và luật thắng; changelog breaking changes; cập nhật/bỏ test bị thay có lý do, không silent skip; giữ mọi regression không bị thay thế. Test ẩn của giảng viên không được truy cập nên không tự khẳng định đã đạt.
