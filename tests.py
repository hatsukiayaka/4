from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from students.models import Student
from academics.models import Course, CourseSection
from enrollments.models import Enrollment
from .models import GradeComponent, Grade
from .services import calculate_final_grade

class GradeCalculationTests(TestCase):
    def setUp(self):
        student = Student.objects.create(student_code='25070011', full_name='Nguyễn Minh Anh', administrative_class='CNTT-K68', email='a@example.local')
        course = Course.objects.create(course_code='CS101', course_name='Nhập môn lập trình', credits=3)
        section = CourseSection.objects.create(course=course, section_code='CS101-01', semester='1', academic_year='2026-2027', status=CourseSection.Status.OPEN)
        self.enrollment = Enrollment.objects.create(student=student, course_section=section)
        self.assignment = GradeComponent.objects.create(course_section=section, component_name='Bài tập', weight_percent=Decimal('20.00'))
        self.midterm = GradeComponent.objects.create(course_section=section, component_name='Giữa kỳ', weight_percent=Decimal('30.00'))
        self.final = GradeComponent.objects.create(course_section=section, component_name='Cuối kỳ', weight_percent=Decimal('50.00'))

    def test_calculate_weighted_final_grade(self):
        Grade.objects.create(enrollment=self.enrollment, component=self.assignment, score=Decimal('8.00'))
        Grade.objects.create(enrollment=self.enrollment, component=self.midterm, score=Decimal('7.00'))
        Grade.objects.create(enrollment=self.enrollment, component=self.final, score=Decimal('9.00'))
        self.assertEqual(calculate_final_grade(self.enrollment), Decimal('8.20'))

    def test_reject_incomplete_weights(self):
        self.final.weight_percent = Decimal('40.00')
        self.final.save()
        with self.assertRaises(ValidationError):
            calculate_final_grade(self.enrollment)


from django.test import Client
from django.urls import reverse
from accounts.models import User

class GradeAccessControlTests(TestCase):
    def setUp(self):
        self.student_profile = Student.objects.create(
            student_code='25070021', full_name='Phạm Minh K', administrative_class='CNTT-K68',
            email='k@example.local'
        )
        self.course = Course.objects.create(course_code='DB201', course_name='Cơ sở dữ liệu', credits=3)
        self.section = CourseSection.objects.create(
            course=self.course, section_code='DB201-01', semester='1', academic_year='2026-2027'
        )
        self.enrollment = Enrollment.objects.create(student=self.student_profile, course_section=self.section)
        self.lecturer = User.objects.create_user(username='lecturer_test', password='StrongPass123!', role=User.Role.LECTURER)
        self.other_lecturer = User.objects.create_user(username='lecturer_other', password='StrongPass123!', role=User.Role.LECTURER)
        self.section.teacher_user = self.lecturer
        self.section.save()
        self.student_user = User.objects.create_user(username='student_test', password='StrongPass123!', role=User.Role.STUDENT)
        self.student_profile.user = self.student_user
        self.student_profile.save()

    def test_assigned_lecturer_can_open_gradebook(self):
        client = Client()
        client.force_login(self.lecturer)
        response = client.get(reverse('grading:gradebook', args=[self.section.pk]))
        self.assertEqual(response.status_code, 200)

    def test_unassigned_lecturer_cannot_open_gradebook(self):
        client = Client()
        client.force_login(self.other_lecturer)
        response = client.get(reverse('grading:gradebook', args=[self.section.pk]))
        self.assertEqual(response.status_code, 403)

    def test_student_can_view_own_grades(self):
        client = Client()
        client.force_login(self.student_user)
        response = client.get(reverse('grading:my_grades'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_open_staff_search(self):
        client = Client()
        client.force_login(self.student_user)
        response = client.get(reverse('grading:search'))
        self.assertEqual(response.status_code, 403)
