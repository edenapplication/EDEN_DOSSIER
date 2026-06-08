from django.shortcuts import render, get_object_or_404
from .models import Property


def property_list(request):
    properties = Property.objects.filter(is_active=True).prefetch_related('images')
    return render(request, 'properties/list.html', {'properties': properties})


def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, is_active=True)
    images = property_obj.images.all()
    related = Property.objects.filter(is_active=True).exclude(pk=pk)[:3]
    return render(request, 'properties/detail.html', {
        'property': property_obj,
        'images': images,
        'related': related,
    })