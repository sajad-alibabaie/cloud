from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from account.forms import SignUpForm


def login_view(request):
    next_url = request.GET.get('next')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Successful login
            login(request, user)
            redirect_url = next_url if next_url else reverse('cloud:index')
            return HttpResponseRedirect(redirect_url)
        else:
            # undefined user or wrong password
            context = {
                'username': username,
                'error': 'Username OR Password is incorrect.'
            }
    else:
        context = {}
    return render(request, 'account/login.html', context)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('account:login'))


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user.refresh_from_db()
                user.profile.Total_storage = 50.0
                user.profile.Download = 0.0
                user.profile.Upload = 0.0
                user.save()
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=user.username, password=raw_password)
                login(request, user)
                return redirect('cloud:index')
            except Exception as e:
                error = e
                return render(request, 'account/signup.html', {'form': form, 'error': error})
        else:
            return render(request, 'account/signup.html', {'form': form, 'error': form.errors})

    else:
        form = SignUpForm()
    return render(request, 'account/signup.html', {'form': form})
