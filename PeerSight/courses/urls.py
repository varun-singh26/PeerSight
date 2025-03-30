from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("create_course/", views.create_course_view, name="create_course"),
    path("manage_courses/", views.manage_courses_view, name="manage_courses"),
    path("course_detail/", views.course_detail_view, name="course_detail"),
    path("course/<int:course_id>/", views.course_detail_view, name="course_detail"),
    path("course/<int:course_id>/add-student/", views.add_student_view, name="add_student"),
]