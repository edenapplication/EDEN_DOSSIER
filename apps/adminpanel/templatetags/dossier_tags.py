from django import template
from django.utils import timezone
import datetime

register = template.Library()


@register.simple_tag
def get_alerte_count():
    try:
        from apps.dossiers.models import Dossier
        seuil = timezone.now() - datetime.timedelta(days=45)
        tous = Dossier.objects.filter(created_at__lte=seuil)
        return sum(1 for d in tous if not d.is_complete())
    except Exception:
        return 0