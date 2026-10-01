Muse2API Cookie Importer —— Hướng dẫn cài đặt
===================================================

Tiện ích này chỉ làm một việc duy nhất: Đồng bộ Cookie đăng nhập muse.ai
từ trình duyệt của bạn vào dịch vụ muse2api. Không cần cài Python, không cần mở terminal.


I. Giải nén
-----------
Giải nén muse2api-extension.zip vào thư mục cố định trên máy của bạn, ví dụ:

    Windows : D:\muse2api-extension
    macOS   : ~/Documents/muse2api-extension
    Linux   : ~/workspace/ai-world/muse2api/extension

Sau khi giải nén sẽ có các tệp: manifest.json, popup.html, popup.js.


II. Cài đặt vào Chrome / Edge
-----------------------------
Google Chrome:
  1. Nhập  chrome://extensions  vào thanh địa chỉ rồi nhấn Enter
  2. Bật công tắc «Chế độ cho nhà phát triển» ở góc trên bên phải
  3. Nhấn vào «Tải tiện ích đã giải nén» ở góc trên bên trái
  4. Chọn thư mục vừa giải nén (chọn cả thư mục, không phải từng file riêng lẻ)
  5. Nhấn vào biểu tượng mảnh ghép và ghim tiện ích ra thanh công cụ

Microsoft Edge:
  1. Nhập  edge://extensions  vào thanh địa chỉ rồi nhấn Enter
  2. Bật công tắc «Chế độ nhà phát triển» ở góc dưới bên trái
  3. Nhấn «Tải phần mở rộng chưa đóng gói»
  4. Các bước tiếp theo tương tự như Chrome

Các trình duyệt Chromium khác (Brave, Cốc Cốc, Vivaldi, Opera) thực hiện tương tự.


III. Cách sử dụng
-----------------
1. Trên trình duyệt này, mở https://muse.ai/ và đăng nhập tài khoản cho tới khi vào được giao diện chat (https://muse.ai/thread/new).
2. Vào trang quản trị muse2api (http://localhost:18610/admin), sao chép BASE URL và API Key ở đầu trang.
3. Nhấn vào biểu tượng tiện ích Muse2API trên thanh công cụ, điền 2 thông tin trên vào (tiện ích sẽ tự lưu cho lần sau).
4. Nhấn nút «Đọc và Nhập Cookie». Khi thông báo «✓ Nhập tài khoản thành công» xuất hiện là hoàn tất.


IV. Câu hỏi thường gặp
----------------------
Q: Báo lỗi «Không tìm thấy Cookie nào của muse.ai»
A: Trình duyệt chưa đăng nhập tài khoản muse.ai. Hãy mở https://muse.ai/ và đăng nhập trước.

Q: Báo lỗi «Thiếu mục cốt lõi hatch_vml...»
A: Chưa mở tới giao diện chat. Hãy vào https://muse.ai/thread/new, gửi thử 1 câu chat rồi bấm nhập lại.

Q: Báo lỗi «API Key không chính xác (Mã lỗi 401)»
A: Vào trang quản trị sao chép lại API Key (bắt đầu bằng m2a_...).

Q: Báo lỗi mạng / CORS
A: Kiểm tra địa chỉ dịch vụ và xác nhận container docker muse2api đang chạy bình thường.

Q: Tiện ích có làm lộ cookie hay gửi đi nơi khác không?
A: Tuyệt đối không. Tiện ích chỉ dùng quyền cookies và storage nội bộ, chỉ gửi POST duy nhất về địa chỉ server do chính bạn cung cấp. Mã nguồn hoàn toàn mở trong popup.js.


V. Gỡ cài đặt
-------------
chrome://extensions → Tìm «Muse2API Cookie Importer» → Nhấn Xóa (Remove).
