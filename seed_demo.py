from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import User
from students.models import Student
from academics.models import Course, CourseSection
from enrollments.models import Enrollment

class Command(BaseCommand):
    help = 'Tạo bộ dữ liệu demo cục bộ cho mốc 1. Không sử dụng dữ liệu thật.'

    def add_arguments(self, parser):
        parser.add_argument('--password', required=True, help='Mật khẩu dùng riêng cho tài khoản demo cục bộ.')

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        if len(password) < 8:
            raise CommandError('Mật khẩu demo phải có ít nhất 8 ký tự.')
        staff, _ = User.objects.get_or_create(
            username='giaovu_demo',
            defaults={'email': 'giaovu.demo@example.local', 'role': User.Role.ACADEMIC_STAFF},
        )
        staff.role = User.Role.ACADEMIC_STAFF
        staff.set_password(password)
        staff.save()

        course, _ = Course.objects.get_or_create(
            course_code='CS101',
            defaults={'course_name': 'Nhập môn lập trình', 'credits': 3, 'is_active': True},
        )
        section, _ = CourseSection.objects.get_or_create(
            course=course, section_code='CS101-01', semester='1', academic_year='2026-2027',
            defaults={'teacher_user': staff, 'status': CourseSection.Status.OPEN},
        )
        section.teacher_user = staff
        section.status = CourseSection.Status.OPEN
        section.save()

        sample_students = [
            ('25070011', 'Nguyễn Minh Anh', 'CNTT-K68', 'minhanh@example.local'),
            ('25070012', 'Trần Gia Bảo', 'CNTT-K68', 'giabao@example.local'),
            ('25070013', 'Lê Thu Hà', 'CNTT-K68', 'thuha@example.local'),
        ]
        for code, name, admin_class, email in sample_students:
            student, _ = Student.objects.get_or_create(
                student_code=code,
                defaults={'full_name': name, 'administrative_class': admin_class, 'email': email},
            )
            Enrollment.objects.get_or_create(student=student, course_section=section)

        self.stdout.write(self.style.SUCCESS(
            'Đã tạo/cập nhật dữ liệu demo. Đăng nhập bằng giaovu_demo và mật khẩu được truyền qua --password.'
        ))
