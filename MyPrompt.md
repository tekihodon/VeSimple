Tôi có file HTML @c:/Users/LucasLaptop/Documents/Codes/VeSimple/3d_seating_chart.html  là trang bán vẻ 1 Liveshow tên là "9 giờ kém 15". Bám vào file này để dựng tiếp web của tôi. Các thông tin config nằm trong file config.json
Hãy bổ sung những chức năng sau:
- Server Flask để chạy html. Chạy trên cổng 3333.
- Hoàn thiện luồng mua vé; hiển thị đúng số ghế còn lại trên trang sơ đồ 3D
- trang phụ <endpoint>:3333/admin có login password trong config.json. Vào đây có hai chức năng chính:
    + Chọn cụ thể các ghế sẽ cấp cho từng order (chọn order, bấm vào ghế trên sơ đồ 3D, hiển thị thêm ghế đã bị chọn).
    + Số ghế còn của mỗi loại phải cập nhật liên tục
    + Chức năng gửi email (bằng ReSendAPI) thông báo cho các đơn hàng được admin chọn ghế xong. Xem kỹ sơ đồ để nắm được số ghế. (Chức năng này làm sau cùng khi tôi kiểm tra kỹ hết các vấn đề kết nối với Resend)

Brainstorm để chức năng mua vé sẽ như sau:
- Người dùng vào trang sẽ nhìn thấy trang đầu tiên là thông tin chương trình (đọc kỹ config.json), show banner là file banner.jpg nếu là điện thoại, banner_ngang.png nếu là Desktop
- Sửa code để khách có thể mua nhiều vé, nhiều loại ghế ở 1 giỏ hàng (ban tổ chức sẽ sắp xếp lại sau)
- Sau khi người dùng checkout thì yêu cầu nhập: Họ và tên, Số điện thoại, Email
- Sau khi người dùng nhập xong thông tin, chốt tổng số tiền, tạo QR động hiện ra để người dùng chuyển khoản bằng VietQR:
Ảnh VietQR động (chi tiết kỹ thuật)
**Đã chốt tài khoản nhận tiền (cố định trong `config.json`):**
```
GET https://img.vietqr.io/img/970424-0988358941.png
    ?amount={tổng số tiền của đơn}
    &addInfo={orderCode}          ← mã đơn (nghĩ ra 1 cách tạo ra đơn theo thời gian và số điện thoại người mua để không bao giờ trùng và đủ ngắn khi người dùng gửi qua app ngân hàng điện thoại) = NỘI DUNG CHUYỂN KHOẢN
    &accountName=BUI%20TUAN%20DUY
    &template=print
```
+ Ngân hàng: **Shinhan Bank** (BIN `970424`) • STK **0988358941** • Chủ TK **BÙI TUẤN DUY** (hiển thị dưới QR).
+ `addInfo` = mã đơn duy nhất; → admin đối soát giao dịch bank theo đúng nội dung này.
+Ảnh QR cache theo order code để khỏi gọi lại.
- Sau khi người dùng chuyển khoản xong sẽ bấm vào nút <Tôi đã chuyển khoản xong cho đơn hàng <mã đơn hàng>>
- Hiện ra thông báo confirm đơn hàng. Thông tin người liên hệ lấy trong config.json