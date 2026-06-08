from django.shortcuts import render
from apps.properties.models import Property
from apps.promotions.models import Promotion


def home_view(request):
    properties = Property.objects.filter(is_active=True).order_by('-created_at')[:8]
    promotions = Promotion.objects.filter(is_active=True).order_by('order')
    return render(request, 'core/home.html', {
        'properties': properties,
        'promotions': promotions,
    })


def about_view(request):
    return render(request, 'core/about.html')