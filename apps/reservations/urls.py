from django.urls import path
from . import views

urlpatterns = [
    path('reserver/', views.reservation_create, name='reservation_create'),
    path('reserver/terrain/<int:property_id>/', views.reservation_create, name='reservation_property'),
    path('reserver/promotion/<int:promotion_id>/', views.reservation_create, name='reservation_promotion'),
    path('reserver/confirmation/', views.reservation_success, name='reservation_success'),
]