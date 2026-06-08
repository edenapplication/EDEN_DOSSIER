from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, UserProfileForm
from apps.dossiers.models import Dossier
from apps.promotions.models import Promotion


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_admin_role():
            return redirect('admin_dashboard')
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_admin_role():
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Identifiants incorrects.")
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard_view(request):
    if request.user.is_admin_role():
        return redirect('admin_dashboard')
    dossiers = Dossier.objects.filter(client=request.user)
    promotions = Promotion.objects.filter(is_active=True).order_by('order')
    return render(request, 'users/dashboard.html', {
        'dossiers': dossiers,
        'promotions': promotions,
    })


@login_required
def profile_view(request):
    if request.user.is_admin_role():
        return redirect('admin_dashboard')
    form = UserProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour.")
        return redirect('profile')
    return render(request, 'users/profile.html', {'form': form})