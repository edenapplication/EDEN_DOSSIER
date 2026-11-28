from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.users.api_views import (
    PingView,
    ImportClientsFromLaravelView,
    ListeClientsDjangoView,
)

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('', include('apps.users.urls')),
    path('terrains/', include('apps.properties.urls')),
    path('promotions/', include('apps.promotions.urls')),
    path('dossiers/', include('apps.dossiers.urls')),
    path('reservations/', include('apps.reservations.urls')),
    path('chatbot/', include('apps.chatbot.urls')),
    path('admin-panel/', include('apps.adminpanel.urls')),
     path('api/ping/', PingView.as_view(), name='api_ping'),
     path('api/import/clients/', ImportClientsFromLaravelView.as_view(), name='api_import_clients'),
    path('api/clients/existants/', ListeClientsDjangoView.as_view(), name='api_clients_existants'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)