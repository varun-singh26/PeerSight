from django.urls import path

from . import views

app_name = "student"

urlpatterns = [
    path("student_forms/", views.student_form_dashboard_view, name="student_form_dashboard"),
    path('student-feedback/<int:form_id>/<int:student_id>/', views.student_feedback_view, name='student_feedback'),
    path('your-responses/', views.student_responses_view, name="your_responses"),
    path('your-responses/<int:response_id>/', views.student_response_details_view, name="your_response_details"),
    path('your-feedback/', views.student_received_feedback_view, name="your_received_feedback"),
    path('my-grades/', views.my_grades, name='my_grades')
] 

