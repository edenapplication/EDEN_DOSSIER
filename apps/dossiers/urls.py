from django.urls import path
from . import views

urlpatterns = [
    path('', views.dossier_list, name='dossier_list'),
    path('<int:pk>/', views.dossier_detail, name='dossier_detail'),
]