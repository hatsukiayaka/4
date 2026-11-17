import csv
from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from accounts.permissions import section_access_required, role_required
from academics.models import CourseSection
from enrollments.models import Enrollment
from students.models import Student
from .forms import GradeComponentForm, GradeEntryForm
from .models import Grade, GradeComponent
from .services import calculate_final_grade

@role_required("ADMIN", "ACADEMIC_STAFF", "LECTURER", "STUDENT")
def grade_home(request):
    if request.user.role == "STUDENT":
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            student = None
        enrollments = Enrollment.objects.filter(student=student).select_related("course_section__course") if student else Enrollment.objects.none()
        return redirect("grading:my_grades")
    sections = CourseSection.objects.select_related("course", "teacher_user")
    if request.user.role == "LECTURER" and not request.user.is_superuser:
        sections = sections.filter(teacher_user=request.user)
    return render(request, "grading/section_list.html", {"sections": sections})

@section_access_required
def section_gradebook(request, section_id):
    section = get_object_or_404(CourseSection.objects.select_related("course"), pk=section_id)
    components = list(GradeComponent.objects.filter(course_section=section))
    enrollments = Enrollment.objects.filter(course_section=section, status=Enrollment.Status.ENROLLED).select_related("student").prefetch_related("grades__component")
    rows = []
    for enrollment in enrollments:
        grade_map = {g.component_id: g.score for g in enrollment.grades.all()}
        try:
            final_score = calculate_final_grade(enrollment)
        except ValidationError:
            final_score = None
        rows.append({"enrollment": enrollment, "grade_map": grade_map, "final_score": final_score})
    weight_total = sum((c.weight_percent for c in components), Decimal("0.00"))
    return render(request, "grading/gradebook.html", {
        "section": section, "components": components, "rows": rows,
        "weight_total": weight_total, "weight_valid": weight_total == Decimal("100.00"),
    })

@section_access_required
def component_create(request, section_id):
    section = get_object_or_404(CourseSection, pk=section_id)
    form = GradeComponentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        component = form.save(commit=False)
        component.course_section = section
        current_total = sum(GradeComponent.objects.filter(course_section=section).values_list("weight_percent", flat=True), Decimal("0.00"))
        if current_total + component.weight_percent > Decimal("100.00"):
            form.add_error("weight_percent", "Tổng trọng số sau khi thêm không được vượt quá 100%.")
            return render(request, "grading/form.html", {"form": form, "title": "Thêm thành phần điểm", "section": section})
        try:
            component.save()
            messages.success(request, "Đã thêm thành phần điểm.")
            return redirect("grading:gradebook", section_id=section.pk)
        except IntegrityError:
            form.add_error("component_name", "Tên thành phần điểm đã tồn tại trong lớp này.")
    return render(request, "grading/form.html", {"form": form, "title": "Thêm thành phần điểm", "section": section})

@section_access_required
def grade_entry(request, section_id, enrollment_id):
    section = get_object_or_404(CourseSection, pk=section_id)
    enrollment = get_object_or_404(Enrollment.objects.select_related("student", "course_section"), pk=enrollment_id, course_section=section)
    component_id = request.POST.get("component") or request.GET.get("component")
    instance = Grade.objects.filter(enrollment=enrollment, component_id=component_id).first() if component_id and str(component_id).isdigit() else None
    form = GradeEntryForm(request.POST or None, instance=instance, enrollment=enrollment)
    if request.method == "POST" and form.is_valid():
        existing = Grade.objects.filter(enrollment=enrollment, component=form.cleaned_data["component"]).first()
        if existing:
            form.instance = existing
        grade = form.save(commit=False)
        grade.enrollment = enrollment
        grade.updated_by = request.user
        try:
            grade.full_clean()
            grade.save()
            messages.success(request, "Đã lưu điểm thành công.")
            return redirect("grading:gradebook", section_id=section.pk)
        except (ValidationError, IntegrityError) as exc:
            form.add_error(None, getattr(exc, "message", "Điểm đã tồn tại hoặc dữ liệu không hợp lệ."))
    return render(request, "grading/grade_form.html", {"form": form, "section": section, "enrollment": enrollment})

@role_required("STUDENT")
def my_grades(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = None
    enrollments = Enrollment.objects.filter(student=student).select_related("course_section__course").prefetch_related("grades__component") if student else Enrollment.objects.none()
    results = []
    for enrollment in enrollments:
        try:
            final = calculate_final_grade(enrollment)
        except ValidationError:
            final = None
        results.append((enrollment, final))
    return render(request, "grading/my_grades.html", {"results": results, "student_mode": True})

def _filtered_rows(request):
    qs = Enrollment.objects.select_related("student", "course_section__course").prefetch_related("grades__component")
    user = request.user
    if user.role == "LECTURER" and not user.is_superuser:
        qs = qs.filter(course_section__teacher_user=user)
    q = request.GET.get("q", "").strip()
    course_id = request.GET.get("course", "").strip()
    semester = request.GET.get("semester", "").strip()
    year = request.GET.get("year", "").strip()
    if q:
        qs = qs.filter(Q(student__student_code__icontains=q) | Q(student__full_name__icontains=q) | Q(course_section__section_code__icontains=q) | Q(course_section__course__course_name__icontains=q))
    if course_id.isdigit():
        qs = qs.filter(course_section__course_id=int(course_id))
    if semester:
        qs = qs.filter(course_section__semester=semester)
    if year:
        qs = qs.filter(course_section__academic_year=year)
    rows = []
    for e in qs.distinct():
        try:
            final = calculate_final_grade(e)
        except ValidationError:
            final = None
        rows.append({"enrollment": e, "final": final})
    return rows

@role_required("ADMIN", "ACADEMIC_STAFF", "LECTURER")
def search_grades(request):
    from academics.models import Course
    rows = _filtered_rows(request)
    courses = Course.objects.all()
    if request.user.role == "LECTURER" and not request.user.is_superuser:
        courses = courses.filter(sections__teacher_user=request.user).distinct()
    return render(request, "grading/search.html", {"rows": rows, "courses": courses, "filters": request.GET})

@role_required("ADMIN", "ACADEMIC_STAFF", "LECTURER")
def statistics(request):
    rows = _filtered_rows(request)
    complete = [r for r in rows if r["final"] is not None]
    passed = [r for r in complete if r["final"] >= Decimal("4.00")]
    failed = [r for r in complete if r["final"] < Decimal("4.00")]
    average = (sum((r["final"] for r in complete), Decimal("0.00")) / len(complete)).quantize(Decimal("0.01")) if complete else None
    return render(request, "grading/statistics.html", {
        "total": len(rows), "complete": len(complete), "missing": len(rows)-len(complete),
        "passed": len(passed), "failed": len(failed), "average": average,
        "pass_rate": round(len(passed)*100/len(complete), 2) if complete else None,
    })

@role_required("ADMIN", "ACADEMIC_STAFF", "LECTURER")
def export_csv(request):
    rows = _filtered_rows(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="ket_qua_hoc_tap.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Ma sinh vien", "Ho ten", "Hoc phan", "Lop hoc phan", "Hoc ky", "Nam hoc", "Diem tong ket"])
    for row in rows:
        e, final = row["enrollment"], row["final"]
        writer.writerow([e.student.student_code, e.student.full_name, e.course_section.course.course_name,
                         e.course_section.section_code, e.course_section.semester, e.course_section.academic_year,
                         str(final) if final is not None else "Chua du diem"])
    return response
