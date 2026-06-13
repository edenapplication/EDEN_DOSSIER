from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm
from apps.dossiers.models import Dossier
from apps.promotions.models import Promotion
from apps.users.models import User


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_admin_role():
            return redirect('admin_dashboard')
        return redirect('dashboard')

    ctx = {'show_admin': False}

    if request.method == 'POST':
        login_type = request.POST.get('login_type', 'client')

        if login_type == 'client':
            username = request.POST.get('username', '').strip()
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    ctx['form_client_error'] = "Ce compte est désactivé. Contactez Eden Group."
                    ctx['client_username'] = username
                elif not user.is_client_role():
                    ctx['form_client_error'] = "Identifiant introuvable. Contactez Eden Group."
                    ctx['client_username'] = username
                else:
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    return redirect('dashboard')
            except User.DoesNotExist:
                ctx['form_client_error'] = "Identifiant introuvable. Contactez Eden Group."
                ctx['client_username'] = username

        elif login_type == 'admin':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_active:
                if user.is_admin_role():
                    login(request, user)
                    return redirect('admin_dashboard')
                else:
                    ctx['form_admin_error'] = "Ce compte n'a pas accès à l'administration."
                    ctx['admin_username'] = username
                    ctx['show_admin'] = True
            else:
                ctx['form_admin_error'] = "Identifiant ou mot de passe incorrect."
                ctx['admin_username'] = username
                ctx['show_admin'] = True

    return render(request, 'users/login.html', ctx)


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