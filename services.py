from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Grade, GradeComponent


def calculate_final_grade(enrollment):
    """Tính điểm tổng kết từ các điểm thành phần sau khi cấu hình đủ 100%."""
    components = list(GradeComponent.objects.filter(course_section=enrollment.course_section))
    if not components:
        raise ValidationError('Lớp học phần chưa có cấu hình thành phần điểm.')
    weight_total = sum((c.weight_percent for c in components), Decimal('0.00'))
    if weight_total != Decimal('100.00'):
        raise ValidationError('Tổng trọng số phải bằng 100% trước khi tính tổng kết.')
    grades = {g.component_id: g for g in Grade.objects.filter(enrollment=enrollment)}
    missing = [c.component_name for c in components if c.pk not in grades]
    if missing:
        raise ValidationError('Chưa có đủ điểm thành phần: ' + ', '.join(missing))
    total = sum((grades[c.pk].score * c.weight_percent / Decimal('100') for c in components), Decimal('0.00'))
    return total.quantize(Decimal('0.01'))
