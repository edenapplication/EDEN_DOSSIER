from django.shortcuts import render, get_object_or_404
from .models import Promotion


def promotion_list(request):
    promotions = Promotion.objects.filter(is_active=True)
    return render(request, 'promotions/list.html', {'promotions': promotions})


def promotion_detail(request, pk):
    promo = get_object_or_404(Promotion, pk=pk, is_active=True)
    images = promo.images.all()
    return render(request, 'promotions/detail.html', {
        'promo': promo,
        'images': images,
    })