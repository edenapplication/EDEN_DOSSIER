from django.contrib import admin
from .models import Promotion, PromotionImage


class PromotionImageInline(admin.TabularInline):
    model = PromotionImage
    extra = 2


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'badge', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    inlines = [PromotionImageInline]