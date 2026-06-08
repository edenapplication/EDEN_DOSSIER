from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


class EtapeGlobale(models.Model):
    TYPE_CHOICES = [
        ('technique', 'Technique'),
        ('morcellement', 'Morcellement'),
    ]
    name = models.CharField(max_length=200, verbose_name="Nom de l'étape")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    percentage = models.PositiveIntegerField(verbose_name="Pourcentage (%)")
    order = models.IntegerField(default=0, verbose_name="Ordre")
    description = models.TextField(blank=True, verbose_name="Description (HTML autorisé)")

    class Meta:
        ordering = ['type', 'order']
        verbose_name = "Étape globale"
        verbose_name_plural = "Étapes globales"

    def __str__(self):
        return f"[{self.get_type_display()}] {self.name} — {self.percentage}%"


class Dossier(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dossiers'
    )
    title = models.CharField(max_length=200, verbose_name="Intitulé")
    reference = models.CharField(max_length=60, unique=True, verbose_name="Référence", blank=True)
    description = models.TextField(blank=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Superficie (m²)")
    date_paiement = models.DateField(null=True, blank=True, verbose_name="Date de paiement")
    photo = models.ImageField(upload_to='dossiers/', null=True, blank=True, verbose_name="Photo du dossier")
    property_link = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Terrain lié"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dossier"
        verbose_name_plural = "Dossiers"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            if self.date_paiement and isinstance(self.date_paiement, (datetime.date, datetime.datetime)):
                date_str = self.date_paiement.strftime('%Y%m%d')
            elif self.date_paiement and isinstance(self.date_paiement, str):
                try:
                    parsed = datetime.datetime.strptime(self.date_paiement, '%Y-%m-%d')
                    date_str = parsed.strftime('%Y%m%d')
                except ValueError:
                    date_str = timezone.now().strftime('%Y%m%d')
            else:
                date_str = timezone.now().strftime('%Y%m%d')
            last = Dossier.objects.filter(reference__startswith=f'EDG-{date_str}').order_by('-reference').first()
            if last:
                try:
                    num = int(last.reference.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.reference = f'EDG-{date_str}-{num:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.title}"

    def get_jours_existence(self):
        return (timezone.now().date() - self.created_at.date()).days

    def is_alerte_45j(self):
        return self.get_jours_existence() >= 45 and not self.is_complete()

    def planifier_cochages_automatiques(self):
        for type_ in ['technique', 'morcellement']:
            etapes = list(EtapeGlobale.objects.filter(type=type_))
            if len(etapes) <= 1:
                continue
            etapes_auto = etapes[:-1]
            for idx, etape in enumerate(etapes_auto):
                date_coche = self.created_at + datetime.timedelta(weeks=idx + 1)
                cochee, _ = EtapeCochee.objects.get_or_create(dossier=self, etape=etape)
                cochee.date_auto_coche = date_coche
                cochee.save()

    def appliquer_cochages_automatiques(self):
        now = timezone.now()
        cochees = self.etapes_cochees.filter(
            date_auto_coche__isnull=False,
            date_auto_coche__lte=now,
            is_done=False
        ).select_related('etape')
        for cochee in cochees:
            cochee.is_done = True
            cochee.done_at = cochee.date_auto_coche
            cochee.save()
            DossierHistorique.objects.get_or_create(
                dossier=self,
                message=f"Étape '{cochee.etape.name}' cochée automatiquement"
            )

    def get_progression_technique(self):
        etapes = EtapeGlobale.objects.filter(type='technique')
        if not etapes.exists():
            return 0
        return sum(
            e.percentage for e in etapes
            if self.etapes_cochees.filter(etape=e, is_done=True).exists()
        )

    def get_progression_morcellement(self):
        etapes = EtapeGlobale.objects.filter(type='morcellement')
        if not etapes.exists():
            return 0
        return sum(
            e.percentage for e in etapes
            if self.etapes_cochees.filter(etape=e, is_done=True).exists()
        )

    def get_total_technique(self):
        return sum(e.percentage for e in EtapeGlobale.objects.filter(type='technique'))

    def get_total_morcellement(self):
        return sum(e.percentage for e in EtapeGlobale.objects.filter(type='morcellement'))

    def is_technique_complete(self):
        etapes = EtapeGlobale.objects.filter(type='technique')
        if not etapes.exists():
            return False
        return all(self.etapes_cochees.filter(etape=e, is_done=True).exists() for e in etapes)

    def is_morcellement_complete(self):
        etapes = EtapeGlobale.objects.filter(type='morcellement')
        if not etapes.exists():
            return False
        return all(self.etapes_cochees.filter(etape=e, is_done=True).exists() for e in etapes)

    def is_complete(self):
        return self.is_technique_complete() and self.is_morcellement_complete()

    def get_statut_display(self):
        return "Complet" if self.is_complete() else "En cours"

    def get_current_etape_technique(self):
        cochees = self.etapes_cochees.filter(
            etape__type='technique', is_done=True
        ).select_related('etape').order_by('-etape__order')
        if cochees.exists():
            return cochees.first().etape
        return None

    def get_current_etape_morcellement(self):
        cochees = self.etapes_cochees.filter(
            etape__type='morcellement', is_done=True
        ).select_related('etape').order_by('-etape__order')
        if cochees.exists():
            return cochees.first().etape
        return None

    def get_etapes_technique(self):
        result = []
        for eg in EtapeGlobale.objects.filter(type='technique'):
            cochee = self.etapes_cochees.filter(etape=eg).first()
            result.append({
                'etape': eg,
                'is_done': cochee.is_done if cochee else False,
                'is_auto': cochee.date_auto_coche is not None if cochee else False,
            })
        return result

    def get_etapes_morcellement(self):
        result = []
        for eg in EtapeGlobale.objects.filter(type='morcellement'):
            cochee = self.etapes_cochees.filter(etape=eg).first()
            result.append({
                'etape': eg,
                'is_done': cochee.is_done if cochee else False,
                'is_auto': cochee.date_auto_coche is not None if cochee else False,
            })
        return result

    def get_property_images(self):
        if self.property_link:
            imgs = list(self.property_link.images.all())
            if imgs:
                return imgs
        if self.photo:
            return None
        return None


class EtapeCochee(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='etapes_cochees')
    etape = models.ForeignKey(EtapeGlobale, on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)
    date_auto_coche = models.DateTimeField(null=True, blank=True, verbose_name="Date cochage auto prévue")
    done_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        unique_together = ['dossier', 'etape']
        verbose_name = "Étape cochée"
        verbose_name_plural = "Étapes cochées"

    def __str__(self):
        return f"{self.dossier.reference} — {self.etape.name} — {'✓' if self.is_done else '○'}"


class DossierHistorique(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='historique')
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dossier.reference} — {self.message[:50]}"