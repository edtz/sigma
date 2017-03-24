from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, \
    login as django_login, logout as django_logout
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse


def signup(request):
    payload = {}
    
    if request.method == 'POST':
        try:
            User.objects.get(username=request.POST['username'])
            payload['warning'] = 'This username is already used'
        except:
            user = User.objects.create_user(username=request.POST['username'], 
                password=request.POST['password'])
            user = authenticate(username=request.POST['username'], 
                password=request.POST['password'])
            django_login(request, user)
            return redirect('/')

    return render(request, 'registration/signup.html', payload)

def login(request):
    payload = {}

    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], 
            password=request.POST['password'])
        if user is not None:
            if user.is_active:
                django_login(request, user)
                return redirect('/')
            else:
                payload['warning'] = 'Your account was deleted'
        else:
            payload['warning'] = 'The username and password were incorrect'

    return render(request, 'registration/login.html', payload)

def logout(request):

    django_logout(request)
    
    return redirect('/')