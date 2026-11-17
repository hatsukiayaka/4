from django.urls import path
from . import views

app_name = "grading"
urlpatterns = [
    path("", views.grade_home, name="home"),
    path("my/", views.my_grades, name="my_grades"),
    path("section/<int:section_id>/", views.section_gradebook, name="gradebook"),
    path("section/<int:section_id>/components/add/", views.component_create, name="component_create"),
    path("section/<int:section_id>/enrollment/<int:enrollment_id>/grade/", views.grade_entry, name="grade_entry"),
    path("search/", views.search_grades, name="search"),
    path("statistics/", views.statistics, name="statistics"),
    path("export.csv", views.export_csv, name="export_csv"),
]
