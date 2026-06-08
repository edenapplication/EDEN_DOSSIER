from django.contrib import admin
from .models import ChatbotKnowledge, ChatbotUnknown


@admin.register(ChatbotKnowledge)
class ChatbotKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['question_example', 'is_active', 'order']
    list_editable = ['is_active', 'order']


@admin.register(ChatbotUnknown)
class ChatbotUnknownAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_at']
    readonly_fields = ['question', 'created_at']