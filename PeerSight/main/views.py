from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout


# Create your views here.

def admin_landing(request):
    return render(request, "main/admin.html", {})  #Move to main app

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
       
    return render(request, "users/landing_user.html", {}) 

def signin(request):
    return render(request, "users/signin.html", {}) 
    


def logout(request):
    logout(request) #logout the user
    return redirect("/") #return to signin page


'''
(Replaced by def student_landing(request):)
def landing_page(request):
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
  
   return render(request, 'landing_user.html', context)
'''