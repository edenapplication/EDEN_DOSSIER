from django.db import models


class ChatbotKnowledge(models.Model):
    keywords = models.TextField(verbose_name="Mots-clés (séparés par des virgules)")
    question_example = models.CharField(max_length=300, verbose_name="Question type")
    answer = models.TextField(verbose_name="Réponse")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Base de connaissance"
        verbose_name_plural = "Base de connaissances"
        ordering = ['order']

    def __str__(self):
        return self.question_example

    def get_keywords_list(self):
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]


class ChatbotUnknown(models.Model):
    question = models.TextField(verbose_name="Question non reconnue")
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Question inconnue"
        verbose_name_plural = "Questions inconnues"
        ordering = ['-created_at']

    def __str__(self):
        return self.question[:100]