from django.db import models
from django.conf import settings


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
        ('done', 'Effectuée'),
    ]
    name = models.CharField(max_length=200, verbose_name="Nom complet")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    property_link = models.ForeignKey(
        'properties.Property', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Terrain"
    )
    promotion_link = models.ForeignKey(
        'promotions.Promotion', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Promotion"
    )
    visit_date = models.DateField(null=True, blank=True, verbose_name="Date souhaitée")
    message = models.TextField(blank=True, verbose_name="Message")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reservations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d/%m/%Y')}"