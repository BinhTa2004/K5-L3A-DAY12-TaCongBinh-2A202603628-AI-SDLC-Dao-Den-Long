# Ticket-04 — Bình minh: phát hành v1.0.0

Nguồn: ticket Phase4 do người dùng cung cấp. Contract1.3 mở rộng1.2; không thay luật gameplay. Bàn giao phase-4 và GitHub Release v1.0.0.

## Benchmark

`<bench_cmd> --seed 42 --duration 30 --out bench.json`. Cửa sổ/viewport1280×720, không fullscreen; ghi rõ điều khiển vsync. Đêm1 đầy đủ hiệu ứng/ánh sáng như gameplay, chính xác200 Bóng wander rải đều theo seed,100 đom đóm, L1–L3 sáng/fuel100. Tắt input/spawn/damage/pickup/hao dầu/kết thúc; Bóng vẫn wander. Mây đứngorigin. Camera (30*cos(a),15,-30*sin(a)), nhìnorigin, a=0 lúc bắt đầu, tăng2π mỗi15s. Warmup3s không đo, sau đó đo đúng duration rồi tự đóng.

Output1.3: avg_fps=1000*N/sum(dt_ms); k=max(1,ceil(.01*N)), p1_low_fps=1000/mean(k dt lớn nhất); frame_ms_p95 là95th percentile; framesN; load_ms từ tiến trình bắt đầu tới frame đầu; peak_mem_mb RSS hoặc null khi web không đo được (giải thích); vsync_off, renderer, os. Ngưỡng avg≥60,p1≥30,load≤10000 trên máy giảng viên; số đo local tham khảo.

## Soak

`<soak_cmd> --seed 7 --nights 10 --out soak.json`. Cùng một tiến trình, Đêm1→2→3 xoay vòng, seed base+i. Mỗi30tick đổi hướng; mỗi tick jump5%,dash3%,pulse2%,interact10%. Mỗi Đêm tới kết thúc hoặc hết thời lượng. RSSstart sau tải Đêm đầu, RSSend sau reset Đêm cuối. Outputnights/crashes/results/mem_start_mb/mem_end_mb/duration_s. Đạt khi crashes0,end≤1.2*start. Extra creative entities/effects tắt trong cả bench/soak.

## Leaderboard và accessibility

- Nhập tên sau thua bất kỳ Đêm hoặc thắng3; 3–12 ký tự[A-Za-z0-9_]. Lưu name,score(tổng Đêm đã thắng),nights_won0..3,achieved_atISO8601+cótimezone,seed. Top10 scoregiảm, hòa người đạt trước. Lưu đĩa qua restart, mở từmenu; `<run_cmd> --export-leaderboard out.json` xuất entries đúng thứ tự.
- Đổi mọi phím4hướng/jump/dash/interact/pulse/pause; báo trùng, nút reset, lưu.
- Chỉ báo hình ảnh Bóng xuất hiện+arrowmép, gió sắp tới,10s cuối, đèn dầu<30.
- Giảm chuyển động tắt shake/flash toàn màn. Chữ UI≥18px ở1280×720; tùy chọn125% và lưu.

## Bàn giao

Clone sạch→README≤3lệnh→chơi; có yêu cầu hệ thống/ảnh/điều khiển/test/headless/bench/soak. Changelog4phase,CREDITS,LICENSE,harness. Contract1.3 cóbench_cmd/soak_cmd. Commit bench.json/soak.json thật. Retro1–2trang gồm đánh giá4phase,lỗiAI,harness,ước lượngtoken/chi phí,cách tiết kiệm,bài học. DemoMP4<5phút có chơi thật và bằng chứng test/headless/bench. Repo public,phase-4,Releasev1.0.0 có bản chạy được. Testẩn1–3 còn hiệu lực cần đạt; agent không có quyền truy cập để tự xác nhận.
