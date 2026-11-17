# Phạm vi mốc 1 - Tuần 4

## Phạm vi trực tiếp
1. Đăng nhập/đăng xuất; role nền tảng cho STAFF và STUDENT.
2. CRUD Student; kiểm tra student_code duy nhất, email hợp lệ.
3. CRUD Course; tạo/sửa CourseSection; đóng lớp thay vì xóa cứng lớp đã mở.
4. Tạo Enrollment trong lớp OPEN; ngăn trùng cặp student + course_section tại form/service và UNIQUE ở DB.
5. Dashboard đọc số lượng bản ghi từ ORM để chứng minh dữ liệu được truy xuất từ DB.

## Đã chuẩn bị cho bước kế tiếp
- Model GradeComponent/Grade, constraint điểm 0..10 và trọng số 0..100.
- Hàm calculate_final_grade kiểm tra tổng trọng số 100% và đủ điểm trước khi tính.
- App reports tạo khung; truy vấn báo cáo/CSV sẽ hoàn thiện sau.

## Chưa tuyên bố đã thực hiện
Chưa xác nhận các lệnh migrate, runserver, TestCase, Git push hoặc thao tác trực tiếp trên trình duyệt. Cần ghi kết quả thực tế sau khi nhóm chạy ứng dụng.
