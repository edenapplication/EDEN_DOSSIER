from django.db import models


class Promotion(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="Sous-titre")
    description = models.TextField(verbose_name="Description complète")
    image = models.ImageField(upload_to='promotions/', verbose_name="Image")
    badge = models.CharField(max_length=50, blank=True, verbose_name="Badge (ex: -15%)")
    badge_color = models.CharField(max_length=7, default='#C1121F', verbose_name="Couleur badge")
    price = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    advantages = models.TextField(blank=True, verbose_name="Avantages (un par ligne)")
    conditions = models.TextField(blank=True, verbose_name="Conditions")
    order = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def get_advantages_list(self):
        return [a.strip() for a in self.advantages.split('\n') if a.strip()]

    def get_price_display(self):
        if self.price:
            return f"{int(self.price):,} FCFA".replace(',', ' ')
        return None


class PromotionImage(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='promotions/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']