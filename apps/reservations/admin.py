from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'visit_date', 'status', 'created_at']
    list_filter = ['status']
    list_editable = ['status']
    search_fields = ['name', 'phone', 'email']