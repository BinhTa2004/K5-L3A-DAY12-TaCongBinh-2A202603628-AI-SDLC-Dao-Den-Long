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
