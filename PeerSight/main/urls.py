from django.urls import path

from . import views

#Render specific view from the views file based on the path
urlpatterns = [
    path("", views.landing, name='landing'),
    path("mainSignIn/", views.mainSignIn, name='mainSignIn'),
]