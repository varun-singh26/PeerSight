from django.shortcuts import render, redirect
from django.contrib.auth import logout

def home(request):
    return render(request, "home.html")

# function receives a request
def logout_view(request):
    logout(request) #logout the user
    return redirect("/") #return the empty route
