from django.urls import path

from . import views

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
    path("forms/<int:form_id>/fill/", views.fill_form_view, name="fill_form"),
    path('thank-you/', views.thank_you_page, name='thank_you_page'),
    path("course-modification/", views.course_modification, name='course_modification'),



]
