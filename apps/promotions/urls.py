from django.urls import path
from . import views

urlpatterns = [
    path('', views.promotion_list, name='promotion_list'),
    path('<int:pk>/', views.promotion_detail, name='promotion_detail'),
]