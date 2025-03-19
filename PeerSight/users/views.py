from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test

def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:  # Check if user is staff
            return redirect('staff_dashboard')
        else:
            return redirect('student_dashboard')
    return render(request, "home.html")

# function receives a request
def logout_view(request):
    logout(request) #logout the user
    return redirect("/") #return the empty route

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

def is_student(user):
    return user.is_authenticated and not user.is_staff

@login_required
@user_passes_test(is_staff_user)
def staff_dashboard(request):
    # Example data - you would typically get this from your database
    context = {
        'username': request.user.username,
        'total_students': None,  # Will use default in template
        'pending_reviews': None,  # Will use default in template
        'completion_rate': None,  # Will use default in template
        'classes': None,  # Will use default in template
    }
    return render(request, "staff_dashboard.html", context)

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    context = {
        'username': request.user.username,
        'assigned_tasks': None,  # Will use default in template
        'user_classes': None,    # Will use default in template
        'teams': None           # Will use default in template
    }
    return render(request, "student_dashboard.html", context)
