"""
URL configuration for PeerSight project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# ✅ SUPERUSER CREATION HOOK (remove after first deploy)
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()

try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        print("✅ Superuser created!")
except IntegrityError:
    pass

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('student/', include('student.urls')), # 👈 include the student app urls
    path("", include("main.urls")), # If the path is empty, redirect to the main.urls file.
    path("accounts/", include("allauth.urls")), #Will give us all the roots needed to reset the account (reset password, sign out, etc.)
    path("courses/", include("courses.urls")), # 👈 include the courses app urls
]
