from django.contrib import admin
from .models import EtapeGlobale, Dossier, EtapeCochee, DossierHistorique


@admin.register(EtapeGlobale)
class EtapeGlobaleAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'percentage', 'order']
    list_filter = ['type']


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ['reference', 'title', 'client', 'created_at']
    search_fields = ['reference', 'title']


@admin.register(EtapeCochee)
class EtapeCocheeAdmin(admin.ModelAdmin):
    list_display = ['dossier', 'etape', 'is_done', 'done_at']
    list_filter = ['is_done']