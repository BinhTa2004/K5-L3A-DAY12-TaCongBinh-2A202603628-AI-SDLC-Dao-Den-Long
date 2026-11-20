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

# Phase 2 — Ticket-02 / Contract 1.1

Nguồn: `requirements/phase-2.txt` và `requirements/phase-2-standard.md`. Tuning chuẩn thay Phase 1; không sửa/di chuyển tag Phase 1. Giữ các kiểm thử cũ và chạy bằng tuning mới; các giả định về pulse XZ, push tức thì, drop TTL900, jump8 và sinh đom đóm Phase1 hết hiệu lực.

| Mục mới | Acceptance criteria | Bằng chứng |
|---|---|---|
| Số liệu + lướt | Đúng toàn bộ bảng; lướt2.8m/12tick, hồi90tick; không giữ nút để lặp; Y cố định trong dash | test_standard_tuning, dash, air_dash |
| 1. Gió Lạc | Đêm2/3, tối đa2; sinh mỗi1200tick; idle/chase/flee; cướp≤3 một lần; pulse đuổi/drop; bất tử không chặn cướp | drifter-steal/drop.jsonl; tests drifter |
| 2. Bùa Gió | Đúng vị trí, TTL600tick, chạy7.2m/s, dash không hồi nhưng cần nhấn lại; respawn2700tick | charm.jsonl; charm tests |
| 3. Chuỗi ba Đêm | Menu→intro→play→result→intro tiếp; thắng3 hiện Bình Minh; tổng chỉ cộng Đêm thắng; thua chơi lại đúng Đêm | browser.json checks, campaign-dawn.png |
| 4. Pause | Esc/P dừng gameplay; tick tiếp tục nhưng sim_tick và mọi timer/spawn/TTL giữ nguyên; menu đủ4 thao tác | pause.jsonl, pause test, browser check |
| 5. Cài đặt | Đổi volume/độ nhạy và vẫn giữ sau reload | browser.json settings_survive_reload |
| 6. Âm thanh | Nhạc đêm; cue nhặt, thắp, pulse, hit, nhảy, dash, thắng/thua, spawn, đếm10s cuối; cảnh báo gió | Sound trong web/game.js; AudioContext được mở bằng click người dùng; cần người chơi đánh giá chất lượng nghe |
| 7. HUD | Lửa trái, timer giữa đỏ/nhấp nháy≤30s, đèn/điểm phải,10ô dưới, cooldown, nhắc E và chỉ đèn ngoài màn | night-1/2/3.png; browser screenshots |
| 8. Màu + sáng | Màu cơ sở đúng bảng; AmbientLight đúng công thức theo số đèn | materials/C trong renderer, ảnh trước/sau thắp |
| Ba bản đồ | Đúng tâm, bán kính, cầu, dốc, tầng, tháp, bục; không tự thêm vật cản gameplay | tests bridge, ramp/wall/pad/tower; ảnh từng Đêm |
| Gió | Báo trước2s bằng lá/âm; 30s/cơn dài5s, lực2m/s, randomseed; có wind_enabled | wind.jsonl, wind_schedule test |
| Contract1.1 | Thêm đủ snapshot/scenario/input/event; giữ Phase1 regression | tests, parity browser/QuickJS |
| Hiệu năng | ≤30s cho đủ Đêm≤21600tick; GUI≥30FPS1280×720 | report.json, browser.json kèm renderer |

## Quyết định cho chỗ chưa quy định đủ

- Vận tốc chạy đổi ngay (0s, nằm trong giới hạn0.1s). Nhảy tích phân chính xác theo đoạn gia tốc cố định `y += vy*dt + 0.5*g*dt²`.
- ID hòa được sắp thứ tự chuỗi ổn định, không dùng locale. Event `night_start` ở tick0 sau snapshot0 là event vòng đời Đêm; scenario tự nó không phát thưởng/event.
- Bóng spawning60tick rồi wander; wander lượn tất định; phát hiện/bỏ đuổi đo XZ. Pulse đẩy được cả spawning và stunned vì ticket không loại trừ.
- Respawn tính60 bước kể từ hit rơi; cooldown/thời gian vẫn chạy trong thời gian chờ. Tick hồi sinh xuất phát đúng origin, vận tốc0; input đang giữ có hiệu lực lại từ tick kế tiếp.
- Dash khóa vận tốc Y bằng0, giữ động lượng Y để tiếp tục sau dash; không mất vận tốc phóng ngang của bục sau dash.
- Góc bản đồ dùng `x=r*cos(angle), z=r*sin(angle)`; gió dùng cùng quy ước. Các point trống được chọn ngẫu nhiên bằng PRNG seed.
- Đom đóm thường có `ttl_s:null`; drop có TTL480. Gió Lạc thả tại vị trí hiện tại trên mặt đất, hit Bóng rải trên vành chuẩn.
- Mặc định origin(0,0,0) kể cả Đêm3 theo contract; tầng2 là sàn trên cao. Khi Mây ở dưới sàn, renderer hiển thị sàn bán trong suốt để không che người chơi. Không teleport chân lên mái. Có thể đi ra vùng trống rồi lên dốc/bục.
- Dốc rộng3m đo theo phương vuông góc trục dốc, độ cao tuyến tính từ0 đến3. Mép vách chặn bước đi lên; nhảy chỉ vượt được khi chân đủ cao; rời tầng thì rơi. Tháp là collider trụ r2 từY6 đến14.
- Bóng đã nằm trong vùng an toàn nội suy ra biên trong30tick; ở ngoài không đi vào. Gió Lạc bay không bị vùng an toàn cản.
- Cây/sao/quầng sáng là trang trí, không sửa bản đồ va chạm hoặc output. Âm lượng/độ nhạy lưu localStorage của trình duyệt.

## Cách tái lập

`python tools/verify.py --phase phase-2` chạy mọi test, từng case trong `tests/scenarios/features.json`, đo đủ Đêm và so output lặp.

`python tools/browser_check.py --phase phase-2` cần Chrome và websocket-client; chạy GUI thật ở1280×720, kiểm tra parity, UI campaign/settings, đo từng Đêm có số Bóng tối đa. Scenario thắng nhanh trong bài browser là tình huống QA dựng có chủ đích, không phải video chơi toàn bộ màn.

Test ẩn của giảng viên chưa được truy cập, vì vậy chỉ khẳng định các kiểm chứng của repo đạt. Chưa chạy trên máy chấm macOS/Linux; CI chưa được coi là bằng chứng tới khi workflow chạy.

# Phase3 — giữ đảo sáng tới bình minh

Phần Phase1/2 phía trên mô tả các phiên bản lịch sử. Luật hiện tại ưu tiên [Ticket-03](requirements/phase-3.md) và [ADR-003](adr/003-fuel-and-dawn.md). Changelog ở gốc repo liệt kê từng test thay và lý do; không bỏ chạy regression không bị thay.

| Yêu cầu | Tiêu chí nghiệm thu | Kiểm chứng |
|---|---|---|
| Dầu | Hao chính xác1/s, hết0 tắt/reset deposited/giữ ever_lit; thắp100; E ceil lượng thiếu/cap100; full không event | PhaseThree decay, full/refuel, scenario fuel-out/refuel |
| Thắp lại | Ever_lit cần5, ghi relight true và relit_count; thắp đầu10/relightfalse; không thưởng scenario | first_light_and_relight, partial_relight, relight.jsonl |
| Hút dầu | Chỉ wander chọn đèn yếu gần nhất/id; drain≤2m, cộng dồn5/s mỗi con; event mỗi60tick hút; chase giữ mục tiêu | stacked_drain, target_tie, drain-stack.jsonl |
| Chuyển trạng thái | Drain→chase6m; hết đèn/out-of-range→wander; pulse→stunned; hết choáng→wander; refill≥30 ejection≤30tick không hit | drain exit/pulse/expiry/refill tests |
| Ngưỡng an toàn | Dầu đúng30 còn an toàn, nhỏ hơn30 mất; dùng số nguyên chưa tròn | weak_lamp_loses_safe_zone test, circle renderer check |
| Bình minh | Không early-win; cuối Đêm≥ceil(.6*n); extinction/refill/hit tick cuối có hiệu lực; death ưu tiên | all_lit_no_early_win, thresholds all nights, final-tick tests, campaign GUI |
| Sức chứa | min(20,10+2*successful_lights), actual first/relight tăng; scenario prelit không tăng, reset Đêm | capacity cases + renderer20slots |
| Điểm | 5/mote,100first/40relight,5pulse/15drainpulse, bonus50+floor(raw fuel)/lit và50/flame; không time bonus | score/refuel/pulse/dawn tests |
| Hiển thị dầu | Đèn đang sáng có thanh; dưới30 dầu nhấp nháy cả đèn/thanh1Hz; ambient giảm khi out | browser low-fuel blink, screenshots |
| Mù màu | Checkbox lưu; viền/mắt#00B3FF, UIwarning#FFFFFF+⚠; đèn tắt paper.scaleY.8 và tear visible | browser checks/reload + colorblind-low-fuel.png |
| Contract1.2 | Đủ tuning/snapshot/scenario/event mới; dầu làm tròn1chữ số; capacity/drain | PhaseThree version/scenario/event tests; byte parity browser/QuickJS |

Tái lập: `python tools/verify.py --phase phase-3`, `python tools/browser_check.py --phase phase-3`. Verifier chạy mọi test và15 case headless, sinh report/hash/log. Benchmark đủ14400/16200/18000tick với bản đồ và spawn thực, đặt invuln trong scenario để phép đo không dừng sớm vì bị đánh. Browser QA thắng nhanh dùng time_left_s1/60 theo scenario để kiểm tra chuyển Đêm, không phải lượt chơi toàn Đêm.

Các bằng chứng thật trong docs/proof/phase-3. Tag/evidence cũ giữ nguyên. Chưa được chạy test ẩn; không suy ra mọi test ẩn đã đạt từ test tự viết.

# Phase4 — phát hành có số đo / Contract1.3

Nguồn [Ticket-04](requirements/phase-4.md). Mọi luật gameplay1.2 tiếp tục chạy; thay đổi version assertion chỉ xác nhận schema1.3, không bỏ regression.

| Yêu cầu | Acceptance criteria | Bằng chứng |
|---|---|---|
| Benchmark |1280×720,200wander/100motes/3đèn100fuel,input/timers/damage/spawn/outcome tắt; camera30m/Y15/15s;3s warmup,30sđo | bench.json,bench-scene.json,rawbench-frames.json,unit scene/frozen rules |
| Công thức metrics | avg1000N/sumdt; kceil1%,worstmean,p95nearest-rank; loadfirstGPUframe | tools/bench.py + known-frame unit,releasegate recalculatesraw |
| Soak |10Đêm liên tiếp1process/1Context; seed7..16; randominput đúng xác suất; RSSsau load/reset | soak.json,tools/soak.py;0crash/RSS≤120% |
| Leaderboard | TênASCII3–12,score chỉ Đêm thắng,nights0–3,UTCISO+timezone,seed;top10/earlier tie; đĩa vàCLI chungfile | unitvalidation/top10/tie; browser save477điểm Đêm1 rồi thuaĐêm2; restart server và export so đúngentries |
| Remapping |9actions,lưu,phím trùng không được gán,reset; KeyJnhảy thật và Space cũ không nhảy | browser check + pure binding unit |
| Dễ tiếp cận | captions4nhóm,spawnarrowmép;reduce toànmànhitflash/camera khôngrung;18px/22.5px | browser.spawn/caption/reduced/font checks + screenshots |
| Đóng gói | Clone sạch2lệnh chơi; runtimeZIPkhôngdata/token,asset đầyđủ;headlessđộc lập | package.json + fresh extraction |
| Tài liệu/demo | READMEfull,CHANGELOG4phase,CREDITS,LICENSE,retro,MP4<300s | docs/demo/demo.mp475s,capture.json,releasegateffprobe |
| Bàn giao | phase-4 vàv1.0.0 cùngcommit,release cóZIP/MP4/bench/soak,repo public | publish_release.py kiểmtra tag/head,GitHubreceipt và readback sau xuất |

Benchmark dùng module src/benchmark.js chỉ trong mode riêng; không gọi normalGame.step nên các luật bị tắt không chạy nhầm. Vẫn dùng moveShade/safezone chuẩn và giữ wander thay vì chuyển chase; target là đèn tắt theo Phase3. Renderer batch dùng cùng sphere/eyes/glow trong cả hai mode; không giảm hiệu ứng riêng khi đo. Nhân vật/địch sáng tạo thêm không tồn tại trong mode này và headless.

Leaderboards ghiatomic qua tools/leaderboard.py và lưu artifacts/user-data mặc định. Không ghi vào localStorage để CLI đọc cùng dữ liệu; localStorage chỉ lưu settings. Thời điểm luôn do server tạoUTC microseconds, không tin timestamp từclient. Endpoint local chặn path traversal và request ghi cross-origin; không public server ra mạng.

Browser caps rAF khi chơi thường; launcher bench tắt frame-rate-limit/gpu-vsync, đo riêng với quayvideo tắt. load_ms tính từ lúc CLI chạy tới khi frame đầu hoàn tất gl.finish; RSSwebnull được giải thích README. Ngưỡng chính thức thuộc máy giảng viên.

Tái lập `python tools/verify.py --phase phase-4`, `python tools/browser_check.py --phase phase-4`, bench vàsoak theo contract. tools/release_gate.py kiểmtra rawmetrics,77test/headless,GUI,demo/ZIP vàtài liệu trước tag/publish. Video là frame Chrome theo thời gian thật; lệnh test/headless chạy thật trong video, benchmark preview cónhãn và kết quả đo riêng. Không gọi video đó là chơi trọn ba Đêm.
