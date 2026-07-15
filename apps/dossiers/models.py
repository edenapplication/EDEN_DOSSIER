from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


class IntituleDossier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Intitulé")
    description = models.TextField(null=True, blank=True, default=None)
    image = models.ImageField(upload_to='intitules/', null=True, blank=True, verbose_name="Image de fond")

    class Meta:
        verbose_name = "Intitulé de dossier"
        verbose_name_plural = "Intitulés de dossier"
        ordering = ['name']

    def __str__(self):
        return self.name


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
    duree_jours = models.PositiveIntegerField(
        default=7,
        help_text="Nombre de jours avant passage automatique à cette étape"
    )

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
    intitule = models.ForeignKey(
        IntituleDossier,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Intitulé"
    )
    reference = models.CharField(max_length=60, unique=True, verbose_name="Référence", blank=True)
    description = models.TextField(null=True, blank=True, default=None)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Superficie (m²)")
    date_paiement = models.DateField(null=True, blank=True, verbose_name="Date de paiement")
    photo = models.ImageField(upload_to='dossiers/', null=True, blank=True, verbose_name="Photo du dossier")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dossier"
        verbose_name_plural = "Dossiers"
        ordering = ['-created_at']

    def get_title(self):
        return self.intitule.name if self.intitule else "Dossier sans intitulé"

    def get_background_image(self):
        if self.photo:
            return self.photo.url
        if self.intitule and self.intitule.image:
            return self.intitule.image.url
        return None

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
        return f"{self.reference} — {self.get_title()}"

    def get_jours_existence(self):
        return (timezone.now().date() - self.created_at.date()).days

    def is_alerte_45j(self):
        return self.get_jours_existence() >= 45 and not self.is_complete()

    def planifier_cochages_automatiques(self):
        """
        Règles strictes :
        - Technique : toutes auto sauf la DERNIÈRE (manuelle)
        - Morcellement : bloqué tant que technique < 100%
                        bloqué tant que la 1ère étape n'est pas cochée MANUELLEMENT (done_by non null)
                        les intermédiaires sont auto
                        la DERNIÈRE est manuelle
        """
        now = timezone.now()
        etapes_tech = list(EtapeGlobale.objects.filter(type='technique').order_by('order'))
        etapes_morc = list(EtapeGlobale.objects.filter(type='morcellement').order_by('order'))

        # ── TECHNIQUE ──
        date_reference = self.created_at
        for i, etape in enumerate(etapes_tech):
            is_last = (i == len(etapes_tech) - 1)
            if is_last:
                break  # dernière = manuelle, jamais touchée

            date_cible = date_reference + datetime.timedelta(days=etape.duree_jours)
            cochee, _ = EtapeCochee.objects.get_or_create(dossier=self, etape=etape)

            if now >= date_cible and not cochee.is_done:
                cochee.is_done = True
                cochee.done_at = date_cible
                cochee.date_auto_coche = date_cible
                cochee.done_by = None  # auto = pas de done_by
                cochee.save()
                DossierHistorique.objects.get_or_create(
                    dossier=self,
                    message=f"Étape '{etape.name}' cochée automatiquement"
                )

            if cochee.is_done:
                date_reference = cochee.done_at or date_cible
            else:
                break  # pas encore atteinte → les suivantes non plus

        # ── MORCELLEMENT ──
        # Condition 1 : technique doit être à 100%
        if not self.is_technique_complete():
            return

        # Condition 2 : il doit y avoir des étapes morcellement
        if not etapes_morc:
            return

        # Condition 3 : la première étape doit être cochée MANUELLEMENT
        # (done_by non null = cochée par un admin, pas automatiquement)
        premiere_morc = etapes_morc[0]
        cochee_premiere = EtapeCochee.objects.filter(
            dossier=self,
            etape=premiere_morc,
            is_done=True,
            done_by__isnull=False  # obligatoirement cochée par un humain
        ).first()

        if not cochee_premiere:
            return  # première étape pas encore cochée manuellement → rien n'avance

        date_reference = cochee_premiere.done_at or now

        # Étapes intermédiaires : auto
        # Dernière étape : manuelle
        for i, etape in enumerate(etapes_morc):
            if i == 0:
                continue  # première = manuelle, jamais touchée ici
            is_last = (i == len(etapes_morc) - 1)
            if is_last:
                break  # dernière = manuelle, jamais touchée

            date_cible = date_reference + datetime.timedelta(days=etape.duree_jours)
            cochee, _ = EtapeCochee.objects.get_or_create(dossier=self, etape=etape)

            if now >= date_cible and not cochee.is_done:
                cochee.is_done = True
                cochee.done_at = date_cible
                cochee.date_auto_coche = date_cible
                cochee.done_by = None  # auto
                cochee.save()
                DossierHistorique.objects.get_or_create(
                    dossier=self,
                    message=f"Étape '{etape.name}' cochée automatiquement"
                )

            if cochee.is_done:
                date_reference = cochee.done_at or date_cible
            else:
                break  # pas encore atteinte → les suivantes non plus


    def appliquer_cochages_automatiques(self, exclude_first_morc=False):
        """
        Applique les coches automatiques.
        Le paramètre exclude_first_morc permet d'éviter de cocher la première étape du morcellement.
        """
        self.planifier_cochages_automatiques()

        now = timezone.now()
        cochees = self.etapes_cochees.filter(
            date_auto_coche__isnull=False,
            date_auto_coche__lte=now,
            is_done=False
        ).select_related('etape')

        for cochee in cochees:
            # Protection supplémentaire : ne jamais cocher automatiquement la première étape du morcellement
            if exclude_first_morc and cochee.etape.type == 'morcellement':
                # Vérifier si c'est la première étape
                first_morc = EtapeGlobale.objects.filter(type='morcellement').order_by('order').first()
                if first_morc and cochee.etape.pk == first_morc.pk:
                    continue

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
        return sum(e.percentage for e in etapes if self.etapes_cochees.filter(etape=e, is_done=True).exists())

    def get_progression_morcellement(self):
        etapes = EtapeGlobale.objects.filter(type='morcellement')
        if not etapes.exists():
            return 0
        return sum(e.percentage for e in etapes if self.etapes_cochees.filter(etape=e, is_done=True).exists())

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
        cochees = self.etapes_cochees.filter(etape__type='technique', is_done=True).select_related('etape').order_by('-etape__order')
        return cochees.first().etape if cochees.exists() else None

    def get_current_etape_morcellement(self):
        cochees = self.etapes_cochees.filter(etape__type='morcellement', is_done=True).select_related('etape').order_by('-etape__order')
        return cochees.first().etape if cochees.exists() else None

    def get_etapes_technique(self):
        result = []
        for eg in EtapeGlobale.objects.filter(type='technique'):
            cochee = self.etapes_cochees.filter(etape=eg).first()
            result.append({'etape': eg, 'is_done': cochee.is_done if cochee else False, 'is_auto': cochee.date_auto_coche is not None if cochee else False})
        return result

    def get_etapes_morcellement(self):
        result = []
        for eg in EtapeGlobale.objects.filter(type='morcellement').order_by('order'):
            cochee = self.etapes_cochees.filter(etape=eg).first()
            is_done = cochee.is_done if cochee else False
            result.append({
                'etape': eg, 
                'is_done': is_done, 
                'is_auto': cochee.date_auto_coche is not None if cochee else False
            })
        return result
    def get_all_clients(self):
        """Retourne tous les users ayant accès à ce dossier."""
        return [a.user for a in self.acces.select_related('user').all()]

    def get_clients_display(self):
        """Noms de tous les clients pour l'affichage liste."""
        users = self.get_all_clients()
        return ' / '.join(
            (u.last_name or u.username).upper() for u in users
        )

    def get_proprietaire(self):
        """Retourne le client principal (proprietaire)."""
        acces = self.acces.filter(est_proprietaire=True).select_related('user').first()
        return acces.user if acces else self.client


class EtapeCochee(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='etapes_cochees')
    etape = models.ForeignKey(EtapeGlobale, on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)
    date_auto_coche = models.DateTimeField(null=True, blank=True)
    done_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['dossier', 'etape']

    def __str__(self):
        return f"{self.dossier.reference} — {self.etape.name}"


class DossierHistorique(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='historique')
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dossier.reference} — {self.message[:50]}"
    
class DossierAcces(models.Model):
    """Lien d'accès entre un utilisateur et un dossier (remplace le champ client direct)."""
    dossier = models.ForeignKey('Dossier', on_delete=models.CASCADE, related_name='acces')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dossiers_acces'
    )
    est_proprietaire = models.BooleanField(default=False)  # le client principal
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('dossier', 'user')
        ordering = ['-est_proprietaire', 'date_ajout']

    def __str__(self):
        return f"{self.user.username} → {self.dossier.reference}"
    
class DossierCodeAcces(models.Model):
    """
    Code/mot d'accès libre lié à un dossier.
    Peut être associé à un user (créé auto) ou juste un mot-clé de recherche.
    """
    dossier = models.ForeignKey(
        'Dossier', on_delete=models.CASCADE, related_name='codes_acces'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='codes_acces_dossier',
        null=True, blank=True
    )
    code = models.CharField(max_length=120)
    label = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        # Un même code peut exister sur plusieurs dossiers
        # (ex: "bonjour" sur dossier 5 et dossier 47)

    def __str__(self):
        return f"{self.code} → {self.dossier.reference}"
    