from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ReservationForm
from apps.properties.models import Property
from apps.promotions.models import Promotion


def reservation_create(request, property_id=None, promotion_id=None):
    property_obj = None
    promotion_obj = None
    if property_id:
        property_obj = get_object_or_404(Property, pk=property_id)
    if promotion_id:
        promotion_obj = get_object_or_404(Promotion, pk=promotion_id)

    form = ReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reservation = form.save(commit=False)
        if property_obj:
            reservation.property_link = property_obj
        if promotion_obj:
            reservation.promotion_link = promotion_obj
        if request.user.is_authenticated:
            reservation.user = request.user
        reservation.save()
        messages.success(request, "Votre demande de visite a été envoyée ! Notre équipe vous contactera sous 24h.")
        return redirect('reservation_success')
    return render(request, 'reservations/form.html', {
        'form': form,
        'property': property_obj,
        'promotion': promotion_obj,
    })


def reservation_success(request):
    return render(request, 'reservations/success.html')