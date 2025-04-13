from django.urls import path

from . import views

app_name = "student"

urlpatterns = [
    path("student_forms/", views.student_form_dashboard_view, name="student_form_dashboard")
]