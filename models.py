from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from enrollments.models import Enrollment
from academics.models import CourseSection

class GradeComponent(models.Model):
    course_section = models.ForeignKey(CourseSection, on_delete=models.PROTECT, related_name='grade_components')
    component_name = models.CharField(max_length=80)
    weight_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['course_section', 'position']
        constraints = [
            models.UniqueConstraint(fields=['course_section', 'component_name'], name='uq_section_component_name'),
            models.CheckConstraint(
                condition=models.Q(weight_percent__gte=0) & models.Q(weight_percent__lte=100),
                name='ck_component_weight_0_100',
            ),
        ]

    def __str__(self):
        return f'{self.component_name} ({self.weight_percent}%)'

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name='grades')
    component = models.ForeignKey(GradeComponent, on_delete=models.PROTECT, related_name='grades')
    score = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['enrollment', 'component'], name='uq_enrollment_grade_component'),
            models.CheckConstraint(
                condition=models.Q(score__gte=0) & models.Q(score__lte=10),
                name='ck_grade_score_0_10',
            ),
        ]

    def clean(self):
        if self.enrollment_id and self.component_id:
            if self.enrollment.course_section_id != self.component.course_section_id:
                from django.core.exceptions import ValidationError
                raise ValidationError('Thành phần điểm phải thuộc đúng lớp của lượt đăng ký.')

    def __str__(self):
        return f'{self.enrollment} - {self.component}: {self.score}'
