from django.contrib import admin
from .models import Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'area', 'price', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['title', 'location']
    inlines = [PropertyImageInline]