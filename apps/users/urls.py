from django.urls import path
from . import views

urlpatterns = [
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profil/', views.profile_view, name='profile'),
]