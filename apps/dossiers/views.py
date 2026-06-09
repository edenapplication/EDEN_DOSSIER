from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.properties.models import PropertyImage
from .models import Dossier


@login_required
def dossier_list(request):
    if request.user.is_admin_role():
        return redirect('admin_dashboard')
    dossiers = Dossier.objects.filter(client=request.user)
    return render(request, 'dossiers/list.html', {'dossiers': dossiers})


@login_required
def dossier_detail(request, pk):
    if request.user.is_admin_role():
        return redirect('admin_dashboard')
    dossier = get_object_or_404(Dossier, pk=pk, client=request.user)
    dossier.appliquer_cochages_automatiques()

    return render(request, 'dossiers/detail.html', {
        'dossier': dossier,
        'etapes_technique': dossier.get_etapes_technique(),
        'etapes_morcellement': dossier.get_etapes_morcellement(),
        
    })