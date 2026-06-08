from django.apps import AppConfig


class DossiersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dossiers'
    label = 'dossiers'

    def ready(self):
        from django.db.models.signals import post_migrate
        pass