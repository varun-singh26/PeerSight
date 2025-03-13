from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def landing(response):
    return HttpResponse("<h1>Landing Page</>")


def mainSignIn(response):
    return HttpResponse("<h1>mainSignIn Page</>")
    return render(response, "main/signIn.html", {}) #render the signIn.html file