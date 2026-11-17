from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

STAFF_ROLES = {"LECTURER", "ACADEMIC_STAFF", "ADMIN"}
MANAGER_ROLES = {"ACADEMIC_STAFF", "ADMIN"}

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.is_superuser or getattr(request.user, "role", None) in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("Bạn không có quyền truy cập chức năng này.")
        return wrapped
    return decorator

def staff_required(view_func):
    return role_required(*STAFF_ROLES)(view_func)

def manager_required(view_func):
    return role_required(*MANAGER_ROLES)(view_func)

def can_access_section(user, section):
    if user.is_superuser or getattr(user, "role", None) in MANAGER_ROLES:
        return True
    return getattr(user, "role", None) == "LECTURER" and section.teacher_user_id == user.id

def section_access_required(view_func):
    @wraps(view_func)
    def wrapped(request, section_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        from academics.models import CourseSection
        from django.shortcuts import get_object_or_404
        section = get_object_or_404(CourseSection, pk=section_id)
        if not can_access_section(request.user, section):
            raise PermissionDenied("Bạn không được phân công hoặc không có quyền quản lý lớp học phần này.")
        return view_func(request, section_id, *args, **kwargs)
    return wrapped
