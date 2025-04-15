from django.urls import path

from . import views

app_name = 'main'  # This is the namespace for the app. It allows us to use the same URL names in different apps without conflict.

#Render specific view from the views file based on the path
urlpatterns = [
    #path("", views.landing, name='landing'),
    path("", views.signin, name='signin'),
    path("admin_landing/", views.admin_landing, name='admin_landing'),
    path("student_landing/", views.student_landing, name='student_landing'),

    path("route_user/", views.route_user, name='route_user'),
    path("logout/", views.user_logout, name='logout'),
    #path("landing_page/", views.landing_page, name='landing_page'),
    path('create-form/', views.create_form_view, name='create_form'),
    path("manage-forms/", views.manage_forms_view, name='manage_forms'),
    path("forms/<int:form_id>/", views.form_detail_view, name='form_detail'),
    path('fill-form/<int:form_id>/', views.fill_form_view, name='fill_form'),
    path('thank-you/', views.thank_you_page, name='thank_you_page'),
    path('view-responses/', views.view_responses, name='view_responses'),
    path('student-responses/', views.student_responses, name='student_responses'),
    path('student-responses/<int:response_id>/', views.student_response_details, name='student_response_details'),
    #path("course-modification/", views.course_modification, name='course_modification'),
    path('forms/', views.student_forms_view, name='student_forms'),
    path('ajax/get_teams/<int:course_id>/', views.get_teams_for_course, name='get_teams_for_course'),
    path('student-feedback/<int:form_id>/<int:student_id>/', views.student_feedback_view, name='student_feedback'),
]
