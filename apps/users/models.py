from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('commercial', 'Commercial'),
        ('client', 'Client'),
    ]
    SEXE_CHOICES = [
        ('masculin', 'Masculin'),
        ('feminin', 'Féminin'),
        ('plusieurs', 'Plusieurs'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    sexe = models.CharField(max_length=20, choices=SEXE_CHOICES, default='masculin', verbose_name="Sexe")

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def is_admin_role(self):
        return self.role in ('admin', 'commercial')

    def is_client_role(self):
        return self.role == 'client'

    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()

    def get_civilite(self):
        if self.sexe == 'masculin':
            return f"Monsieur {self.get_full_name() or self.username}"
        elif self.sexe == 'feminin':
            return f"Madame {self.get_full_name() or self.username}"
        else:
            return "Chers clients"

    def get_salutation(self):
        if self.sexe == 'masculin':
            return f"Monsieur {self.first_name or self.username}"
        elif self.sexe == 'feminin':
            return f"Madame {self.first_name or self.username}"
        else:
            return "Chers clients"