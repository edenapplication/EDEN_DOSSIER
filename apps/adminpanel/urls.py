from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),

    path('terrains/', views.admin_properties, name='admin_properties'),
    path('terrains/creer/', views.admin_property_create, name='admin_property_create'),
    path('terrains/<int:pk>/modifier/', views.admin_property_edit, name='admin_property_edit'),
    path('terrains/<int:pk>/supprimer/', views.admin_property_delete, name='admin_property_delete'),

    path('promotions/', views.admin_promotions, name='admin_promotions'),
    path('promotions/creer/', views.admin_promotion_create, name='admin_promotion_create'),
    path('promotions/<int:pk>/modifier/', views.admin_promotion_edit, name='admin_promotion_edit'),
    path('promotions/<int:pk>/supprimer/', views.admin_promotion_delete, name='admin_promotion_delete'),

    path('clients/', views.admin_clients, name='admin_clients'),
    path('clients/creer/', views.admin_client_create, name='admin_client_create'),
    path('clients/<int:pk>/modifier/', views.admin_client_edit, name='admin_client_edit'),
    path('clients/<int:pk>/supprimer/', views.admin_client_delete, name='admin_client_delete'),

    path('etapes/', views.admin_etapes_globales, name='admin_etapes_globales'),
    path('etapes/creer/', views.admin_etape_globale_create, name='admin_etape_globale_create'),
    path('etapes/<int:pk>/modifier/', views.admin_etape_globale_edit, name='admin_etape_globale_edit'),
    path('etapes/<int:pk>/supprimer/', views.admin_etape_globale_delete, name='admin_etape_globale_delete'),

    path('dossiers/', views.admin_dossiers, name='admin_dossiers'),
    path('dossiers/creer/', views.admin_dossier_create, name='admin_dossier_create'),
    path('dossiers/<int:pk>/', views.admin_dossier_detail, name='admin_dossier_detail'),
    path('dossiers/<int:pk>/supprimer/', views.admin_dossier_delete, name='admin_dossier_delete'),
    path('dossiers/<int:dossier_pk>/etape/<int:etape_pk>/toggle/', views.admin_etape_toggle, name='admin_etape_toggle'),
    path('dossiers/alerte-45j/', views.admin_dossiers_alerte, name='admin_dossiers_alerte'),

    path('reservations/', views.admin_reservations, name='admin_reservations'),
    path('reservations/<int:pk>/statut/', views.admin_reservation_update, name='admin_reservation_update'),

    path('chatbot/', views.admin_chatbot, name='admin_chatbot'),
    path('chatbot/creer/', views.admin_chatbot_create, name='admin_chatbot_create'),
    path('chatbot/<int:pk>/modifier/', views.admin_chatbot_edit, name='admin_chatbot_edit'),
    path('chatbot/<int:pk>/supprimer/', views.admin_chatbot_delete, name='admin_chatbot_delete'),
]