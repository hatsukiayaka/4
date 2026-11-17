from django import forms
from .models import GradeComponent, Grade

class GradeComponentForm(forms.ModelForm):
    class Meta:
        model = GradeComponent
        fields = ["component_name", "weight_percent", "position"]
        labels = {"component_name": "Tên thành phần điểm", "weight_percent": "Trọng số (%)", "position": "Thứ tự"}
        widgets = {"weight_percent": forms.NumberInput(attrs={"min": "0", "max": "100", "step": "0.01"})}

    def clean_weight_percent(self):
        value = self.cleaned_data["weight_percent"]
        if value < 0 or value > 100:
            raise forms.ValidationError("Trọng số phải nằm trong khoảng 0–100%.")
        return value

class GradeEntryForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ["component", "score"]
        labels = {"component": "Thành phần điểm", "score": "Điểm (0–10)"}
        widgets = {"score": forms.NumberInput(attrs={"min": "0", "max": "10", "step": "0.01"})}

    def __init__(self, *args, enrollment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.enrollment = enrollment
        if enrollment:
            self.fields["component"].queryset = GradeComponent.objects.filter(course_section=enrollment.course_section)

    def clean(self):
        cleaned = super().clean()
        component = cleaned.get("component")
        if self.enrollment and component and component.course_section_id != self.enrollment.course_section_id:
            self.add_error("component", "Thành phần điểm không thuộc lớp học phần của sinh viên.")
        return cleaned

    def clean_score(self):
        score = self.cleaned_data["score"]
        if score < 0 or score > 10:
            raise forms.ValidationError("Điểm phải nằm trong khoảng 0 đến 10.")
        return score
