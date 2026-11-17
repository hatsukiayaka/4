from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.models import User
from students.models import Student
from academics.models import Course, CourseSection
from enrollments.models import Enrollment

@login_required
def dashboard(request):
    context = {
        'student_count': Student.objects.count(),
        'course_count': Course.objects.filter(is_active=True).count(),
        'section_count': CourseSection.objects.exclude(status=CourseSection.Status.CLOSED).count(),
        'enrollment_count': Enrollment.objects.filter(status=Enrollment.Status.ENROLLED).count(),
    }
    return render(request, 'dashboard.html', context)
