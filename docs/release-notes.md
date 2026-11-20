Game3D Đảo Đèn Lồng: điều khiển Mây thu thập đom đóm, châm dầu và giữ đảo sáng tới bình minh qua ba Đêm. Bản v1.0.0 dùng Test Contract1.3 và giữ luật nhiên liệu/capacity/điểm của Phase3.

Tải `dao-den-long-v1.0.0.zip`, giải nén rồi chạy `python3 tools/serve.py` (Windows có thể dùng `python`). Mở http://127.0.0.1:8000 bằng Chrome/Edge/Chromium có WebGL. Chơi không cần npm/pip/CDN. Python3.10+; khuyến nghị1280×720.

WASD di chuyển,Space nhảy,Shift lướt,E nạp/châm dầu,Q tỏa sáng,Esc/P pause. Cài đặt cho remap mọi hành động, giảm chuyển động,chữ lớn125% và palette dễ phân biệt. Bảng xếp hạng top10 lưu trên đĩa, vẫn còn sau restart; CLIexport đọc cùng file.

Kiểm chứng local:77unit/regression,15headless scenarios, byte-parity browser/QuickJS, GUIcampaign/settings/remap/font/captions/leaderboard qua restart và export. Benchmark thực tế200Bóng+100motes,1280×720/30s:160.14FPS trung bình,1%low95.37FPS,load2.08s trên Intel HD630/Windows10. Soak10Đêm một tiến trình:0crash,RSS18.852→18.879MB. Máy chấm của giảng viên quyết định kết quả chính thức; không tự khẳng định testẩn đã đạt.

Asset đính kèm: bản chạyZIP, video demo75giây, bench.json và soak.json. Bản web báo peak_mem_mb=null vì không có RSS riêng cho app trình duyệt; không thay RSS bằng JSheap. Benchmark chạy riêng với capturevideo tắt. MP4 ghi gameplay/input và lệnh thực, không thu audio; âm thanh trong game dùng WebAudio.

Mã nguồn,tagphase-1…phase-4,ADR,CHANGELOG,retro,harness và toàn bộ bằng chứng ở repo. Xem README để chạy test/headless/bench/soak và chọn thư mục dữ liệu người chơi.
