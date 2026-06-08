from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)