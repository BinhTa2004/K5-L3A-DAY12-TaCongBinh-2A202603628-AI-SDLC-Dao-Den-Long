# Đảo Đèn Lồng

Game 3D góc nhìn thứ ba: cùng Mây gom đom đóm, thắp năm ngọn đèn và giữ ánh sáng trước Bóng Mực. Bản Phase 1 / Test Contract v1.0.

## Chạy game (Python 3.10+)

```sh
python3 -m pip install -r requirements.txt
python3 tools/serve.py
```

Mở **http://127.0.0.1:8000** bằng Chrome, Edge hoặc Firefox có WebGL. Windows có thể thay `python3` bằng `python`. Three.js được lưu sẵn trong repo, không cần CDN khi chơi. macOS/Linux chạy cùng các lệnh trên; môi trường chưa có wheel QuickJS cần C compiler để pip biên dịch.

WASD / phím mũi tên di chuyển; Space nhảy; kéo chuột xoay camera; cuộn chuột thu phóng; E nạp ánh sáng; Q tỏa sáng; Esc/P nghỉ chân. Bắt đầu hành trình → giới thiệu → chơi → thắng/thua → chơi lại.

## Kiểm chứng và headless

```sh
python3 tools/verify.py --phase phase-1
python3 tools/headless.py --seed 42 --night 1 --ticks 600 --out artifacts/run.jsonl
```

Tùy chọn: `--scenario file.json`, `--inputs file.json`, `--snapshot-every 10`. Gameplay dùng cùng `src/core.js` trên trình duyệt và QuickJS; headless không khởi động trình duyệt/GPU. Khai báo lệnh và tuning ở [game.contract.json](game.contract.json).

Điểm: +10 mỗi đom đóm **nạp** vào đèn; +100 mỗi đèn; +5 mỗi Bóng Mực trúng Tỏa Sáng; thắng cộng `floor(giây còn lại) × 2 + Ngọn Lửa còn lại × 50`. Nhặt đom đóm không cộng điểm. Thắng khi đủ đèn, thua khi hết Ngọn Lửa hoặc hết giờ.

- [Yêu cầu gốc Phase 1](docs/requirements/phase-1.txt)
- [Spec, giả định và tiêu chí nghiệm thu](docs/spec.md)
- [Bằng chứng Phase 1](docs/proof/phase-1/report.json)
- [Nhật ký AI](docs/ai-log.md)
- [Hướng dẫn lab gốc](docs/LAB-README.md)

## Sáng tạo của tôi

Mỗi đèn thức dậy có quầng sáng vàng và vòng sáng trên mặt đất; bầu trời sao, biển mây, Ông Đăng kể chuyện và nhạc được tổng hợp bằng Web Audio. Các chi tiết trang trí chỉ tồn tại trong renderer, không thay đổi output headless. Cây trang trí không có va chạm để không thêm chướng ngại ngoài bản đồ.

Nguồn và giấy phép ở [CREDITS.md](CREDITS.md), [LICENSE](LICENSE). CI được cấu hình chạy regression trên macOS/Linux; trạng thái CI chỉ xác nhận sau khi push và workflow chạy thật.
