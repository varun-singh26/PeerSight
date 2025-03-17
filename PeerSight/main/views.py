from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def mainSignIn(response):
    return HttpResponse("<h1>mainSignIn Page</>")
    return render(response, "main/signIn.html", {}) #render the signIn.html file


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