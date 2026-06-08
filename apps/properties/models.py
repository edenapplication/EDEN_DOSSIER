from django.db import models


class Property(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    location = models.CharField(max_length=200, verbose_name="Localisation")
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Superficie (m²)")
    price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Prix (FCFA)")
    main_image = models.ImageField(upload_to='properties/', verbose_name="Image principale")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Terrain"
        verbose_name_plural = "Terrains"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_price_display(self):
        return f"{int(self.price):,} FCFA".replace(',', ' ')


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image {self.order} - {self.property.title}"