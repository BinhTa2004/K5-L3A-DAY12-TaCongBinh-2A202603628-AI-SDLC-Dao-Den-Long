# Changelog

## Phase4 — v1.0.0 / Contract1.3

- Giữ mọi luật1.2; thêm bench_cmd/soak_cmd. Benchmark đúng200Bóng/100motes/3đèn, camera30m/15m, warmup3s và rawframe metrics. Soak10nights cùng tiến trình/context, RSS thật.
- Renderer instancing dùng chung cho gameplay/benchmark, giữ sphere/eyes/glow, giảm drawcall ở cảnh nhiều thực thể.
- Bảng xếp hạng đĩa top10, tên hợp lệ, thời gian UTC ISO, điểm chỉ từ Đêm thắng; GUI/save/menu và CLIexport chung file.
- Remap9actions, báo trùng/reset/lưu; reduced motion,18px tối thiểu/125%, captions và edge-arrow. Lưu cài đặt qua reload.
- Đóng gói web local, README≤3lệnh, kiểm tra ZIP sạch, retro và video thật dưới5phút. Chuẩn bị tagphase-4 và Releasev1.0.0.
- Testmigration: PhaseThree version assertion1.2→1.3, các luật fuel/score/dawn giữ nguyên. Browser assertion màu đọc vật liệu batch thay childmesh cũ; không bỏ kiểm tra kết quả. Bổ sung7unit tests release và UI kiểm tra persistence/export/remap/caption/font.

## Phase3 — Contract1.2 — breaking changes

- Đèn sáng không còn vĩnh viễn: thêm dầu, châm dầu, tắt và thắp lại; tương tác chọn cả đèn sáng nhận được dầu. Ngưỡng dầu30 quyết định vùng an toàn.
- Bóng wander tìm đèn yếu, có trạng thái drain hút dầu; hết choáng chuyển wander trước lần chọn tiếp. Chase giữ mục tiêu người chơi.
- Bỏ thắng sớm và reasonall_lit. Chỉ thắng tại bình minh với≥60% đèn sáng; hết lửa ưu tiên. Duration300/330/360 thay bằng240/270/300s.
- Điểm nạp10→5; bonus thắp lại40, pulse drain tổng15; bonus bình minh theo dầu+đèn+lửa, bỏ thưởng thời gian.
- Capacity cố định10 thay bằng10+2*mỗi lần thắp, trần20; scenario prelit không tăng.
- Snapshot/scenario/event mở rộng theo1.2; UI thêm thanh dầu/blink, đèn xẹp/rách và cài đặt mù màu được lưu.

### Test cũ bị thay — lý do và cách cập nhật

| Test | Thay đổi có chủ đích |
|---|---|
| PhaseOne.test_lighting_and_winning | Đổi tên thành test_lighting_and_dawn_survival; đặt tình huống ngay trước bình minh, chờdawn_survived thay vìall_lit. Thêm test riêng chứng minh đủ đèn không thắng sớm. |
| PhaseTwo.test_standard_tuning | Chỉ đổi ba duration sang240/270/300; vẫn kiểm tra mọi số chuẩn không bị thay. |
| PhaseTwo.test_death_priority_and_win_at_dawn | Expectedreason→dawn_survived; vẫn yêu cầu no_flames ưu tiên. |
| PhaseTwo.test_pickup_then_deposit_then_pulse_order | Điểm200→150 (10*5+100); giữ nguyên assertion deposit xảy ra trước pulse. |
| Decorator skipUnless version1.1 của PhaseTwo | Xóa decorator để mọi regression Phase2 chạy ở1.2. Không xóa hay skip test không bị thay. |

Các assertion tính điểm dùng T.score tự nhận công thức mới; test khác giữ nguyên. Bằng chứng/tag Phase1–2 không sửa. Thêm tests/test_phase3.py và các casefuel để kiểm tra luật thay thế, không dùng test luôn đạt.

## Phase2 — Contract1.1

Ba Đêm, chuẩn hóa số liệu/bản đồ, dash, Bùa Gió, Gió Lạc, gió, pause/settings, campaign và snapshot1.1; 43 test tại tagphase-2.

## Phase1 — Contract1.0

Game3D Đảo Bến, chế độ headless dùng chung core và bằng chứng14 test tại tagphase-1.
