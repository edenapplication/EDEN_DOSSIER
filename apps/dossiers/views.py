from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
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
    
    dossier = get_object_or_404(
        Dossier.objects.filter(acces__user=request.user),
        pk=pk
    )
    
    # Appliquer les coches automatiques effectives
    dossier.appliquer_cochages_automatiques()
    
    # Recharger le dossier depuis la base pour avoir les données à jour
    dossier.refresh_from_db()

    property_images = []
    if dossier.photo:
        property_images = [{'url': dossier.photo.url, 'is_raw': True}]
    elif dossier.intitule and dossier.intitule.image:
        property_images = [{'url': dossier.intitule.image.url, 'is_raw': True}]

    salutation = request.user.get_salutation()

    return render(request, 'dossiers/detail.html', {
        'dossier': dossier,
        'etapes_technique': dossier.get_etapes_technique(),
        'etapes_morcellement': dossier.get_etapes_morcellement(),
        'property_images': property_images,
        'salutation': salutation,
    })