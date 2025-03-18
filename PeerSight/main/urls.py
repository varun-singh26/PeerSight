from django.urls import path

from . import views

#Render specific view from the views file based on the path
urlpatterns = [
    #path("", views.landing, name='landing'),
    path("", views.signin, name='signin'),
    path("admin_landing/", views.admin_landing, name='admin_landing'),
    path("student_landing/", views.student_landing, name='student_landing'),

    path("logout/", views.logout, name='logout'),
    #path("landing_page/", views.landing_page, name='landing_page'),
]