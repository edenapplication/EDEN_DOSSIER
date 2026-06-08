from django.utils.deprecation import MiddlewareMixin


class AutoCochageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/admin-panel/'):
            try:
                from .models import Dossier
                dossiers = Dossier.objects.filter(
                    etapes_cochees__date_auto_coche__isnull=False,
                    etapes_cochees__is_done=False
                ).distinct()
                for dossier in dossiers:
                    dossier.appliquer_cochages_automatiques()
            except Exception:
                pass