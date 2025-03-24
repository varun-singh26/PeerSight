from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


# Create your views here.

# After user signs, in checks role and redirects accordingly
@login_required
def route_user(request):
    user = request.user
    if user.role == "professor":
        return redirect("admin_landing")
    else:
        return redirect("student_landing")

def admin_landing(request):
    if request.user.is_authenticated:
       username = request.user.username

       try:
           social_account = request.user.socialaccount_set.filter(provider='google').first()
           if social_account:
               username = social_account.extra_data.get('name', username)
       except:
           pass
    else:
       username = "Guest"
    context = {
        'username': username,
    }

    return render(request, 'main/admin.html', context)

def student_landing(request):
    if request.user.is_authenticated:
       username = request.user.username

       try:
           social_account = request.user.socialaccount_set.filter(provider='google').first()
           if social_account:
               username = social_account.extra_data.get('name', username)
       except:
           pass
    else:
       username = "Guest"
    context = {
        'username': username,
    }

    return render(request, 'main/landing_user.html', context)

def signin(request):
    return render(request, "users/signin.html", {}) 
    


def user_logout(request):
    logout(request) #logout the user
    return redirect("/") #return to signin page

