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
        is_new = self.pk is None

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
    # ⚠️ AUCUN appel à planifier_etapes_manquantes() ici.
    def __str__(self):
        return f"{self.reference} — {self.get_title()}"

    def get_jours_existence(self):
        return (timezone.now().date() - self.created_at.date()).days

    def is_alerte_45j(self):
        return self.get_jours_existence() >= 45 and not self.is_complete()

    # =============== MÉTHODES DE GESTION DES ÉTAPES ===============

    def est_etape_manuelle(self, etape):
        """
        Une étape est MANUELLE si c'est la 1ère ou la dernière du type
        (selon EtapeGlobale.order). Sinon elle est AUTO.
        """
        etapes = list(
            EtapeGlobale.objects.filter(type=etape.type).order_by('order', 'pk')
        )
        if len(etapes) < 2:
            return True
        return etape.pk in (etapes[0].pk, etapes[-1].pk)

    def planifier_etapes_manquantes(self):
        """
        Planifie les dates de cochage automatique des étapes INTERMÉDIAIRES.

        Règles (Option A — temporel cumulatif) :
        - 1ère étape du type (plus petit 'order') = MANUELLE, point de départ
        - Dernière étape du type (plus grand 'order') = MANUELLE, jamais planifiée
        - Étapes du milieu = AUTO, planifiées à partir du done_at de la 1ère,
            avec cumul de duree_jours dans l'ordre.

        Ne planifie RIEN tant que la 1ère étape n'est pas cochée manuellement.
        Ne planifie RIEN pour le morcellement tant que le technique < 100%.
        """
        from django.db import transaction
        with transaction.atomic():
            now = timezone.now()

            for type_ in ('technique', 'morcellement'):
                if type_ == 'morcellement' and not self.is_technique_complete():
                    continue

                etapes = list(
                    EtapeGlobale.objects.filter(type=type_).order_by('order', 'pk')
                )
                if len(etapes) < 3:
                    continue

                premiere = etapes[0]
                derniere = etapes[-1]
                intermediaires = etapes[1:-1]

                # La 1ère doit être cochée MANUELLEMENT
                cochee_premiere = EtapeCochee.objects.filter(
                    dossier=self,
                    etape=premiere,
                    is_done=True,
                    done_by__isnull=False,
                    date_auto_coche__isnull=True,
                ).first()

                if not cochee_premiere:
                    # 1ère pas cochée manuellement → on ne planifie RIEN
                    # et on nettoie les dates résiduelles
                    EtapeCochee.objects.filter(
                        dossier=self,
                        etape__in=intermediaires + [derniere],
                        is_done=False,
                    ).update(date_auto_coche=None)
                    continue

                date_ref = cochee_premiere.done_at or now

                for etape in intermediaires:
                    cochee, _ = EtapeCochee.objects.get_or_create(
                        dossier=self, etape=etape
                    )
                    if cochee.is_done:
                        if cochee.done_at:
                            date_ref = cochee.done_at
                        continue
                    if cochee.date_auto_coche is not None:
                        date_ref = cochee.date_auto_coche
                        continue
                    date_cible = date_ref + datetime.timedelta(
                        days=etape.duree_jours or 0
                    )
                    cochee.date_auto_coche = date_cible
                    cochee.save(update_fields=['date_auto_coche'])
                    date_ref = date_cible

                # Dernière : jamais planifiée
                EtapeCochee.objects.filter(
                    dossier=self, etape=derniere, is_done=False
                ).update(date_auto_coche=None)

    def planifier_cochages_automatiques(self):
        """
        Alias de compatibilité.
        À la création : ne fait rien (1ère pas encore cochée manuellement).
        """
        self.planifier_etapes_manquantes()
        self.appliquer_cochages_automatiques()

    def appliquer_cochages_automatiques(self):
        """
        Coche les intermédiaires dont la date_auto_coche est échue.
        Respecte l'ordre : on s'arrête à la 1ère non échue.
        Ne touche JAMAIS la 1ère ni la dernière (manuelles).
        Ne fait rien pour le morcellement tant que le technique < 100%.
        """
        now = timezone.now()

        for type_ in ('technique', 'morcellement'):
            if type_ == 'morcellement' and not self.is_technique_complete():
                continue

            etapes = list(
                EtapeGlobale.objects.filter(type=type_).order_by('order', 'pk')
            )
            if len(etapes) < 3:
                continue

            premiere = etapes[0]
            intermediaires = etapes[1:-1]

            # La 1ère doit être cochée manuellement
            cochee_premiere = EtapeCochee.objects.filter(
                dossier=self,
                etape=premiere,
                is_done=True,
                done_by__isnull=False,
            ).first()
            if not cochee_premiere:
                continue

            for etape in intermediaires:
                cochee, _ = EtapeCochee.objects.get_or_create(
                    dossier=self, etape=etape
                )
                if cochee.is_done:
                    continue
                if not cochee.date_auto_coche or cochee.date_auto_coche > now:
                    break  # pas encore échue → on arrête (respect de l'ordre)

                cochee.is_done = True
                cochee.done_at = cochee.date_auto_coche
                cochee.done_by = None
                cochee.save(update_fields=['is_done', 'done_at', 'done_by'])
                DossierHistorique.objects.create(
                    dossier=self,
                    message=f"Étape '{etape.name}' cochée automatiquement",
                )
    def verifier_et_replanifier(self):
        self.planifier_etapes_manquantes()
        self.appliquer_cochages_automatiques()
    # =============== FIN DES MÉTHODES DE GESTION DES ÉTAPES ===============

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
        etapes = list(
            EtapeGlobale.objects.filter(type='technique').order_by('order', 'pk')
        )
        if not etapes:
            return result

        premiere = etapes[0]
        premiere_done = self.etapes_cochees.filter(
            etape=premiere, is_done=True
        ).exists()

        for idx, eg in enumerate(etapes):
            cochee = self.etapes_cochees.filter(etape=eg).first()
            is_done = cochee.is_done if cochee else False
            is_auto_date = (cochee.date_auto_coche is not None) if cochee else False
            is_premiere = (idx == 0)
            is_derniere = (idx == len(etapes) - 1)
            result.append({
                'etape': eg,
                'is_done': is_done,
                'is_auto': is_auto_date,
                'is_manuelle': is_premiere or is_derniere,
                'is_premiere': is_premiere,
                'is_derniere': is_derniere,
                'premiere_done': premiere_done,
            })
        return result

    def get_etapes_morcellement(self):
        result = []
        etapes = list(
            EtapeGlobale.objects.filter(type='morcellement').order_by('order', 'pk')
        )
        if not etapes:
            return result

        premiere = etapes[0]
        premiere_done = self.etapes_cochees.filter(
            etape=premiere, is_done=True
        ).exists()

        for idx, eg in enumerate(etapes):
            cochee = self.etapes_cochees.filter(etape=eg).first()
            is_done = cochee.is_done if cochee else False
            is_auto_date = (cochee.date_auto_coche is not None) if cochee else False
            is_premiere = (idx == 0)
            is_derniere = (idx == len(etapes) - 1)
            result.append({
                'etape': eg,
                'is_done': is_done,
                'is_auto': is_auto_date,
                'is_manuelle': is_premiere or is_derniere,
                'is_premiere': is_premiere,
                'is_derniere': is_derniere,
                'premiere_done': premiere_done,
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
    est_proprietaire = models.BooleanField(default=False)
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

    def __str__(self):
        return f"{self.code} → {self.dossier.reference}"