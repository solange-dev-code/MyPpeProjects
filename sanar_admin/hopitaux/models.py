from django.db import models


class Hopital(models.Model):
    nom = models.CharField(max_length=255)
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Hôpital"
        verbose_name_plural = "Hôpitaux"
        ordering = ['nom']


class LitHopital(models.Model):
    """Suivi des capacités d'accueil en lits par service d'un hôpital.

    Utilisé par l'algorithme d'assignation multi-hôpitaux pour équilibrer
    la charge entre établissements (cf. hopitaux.services.assigner_hopital).
    """

    SERVICE_CHOICES = [
        ('urgences', 'Urgences'),
        ('reanimation', 'Réanimation'),
        ('chirurgie', 'Chirurgie'),
        ('medecine', 'Médecine'),
        ('maternite', 'Maternité'),
        ('pediatrie', 'Pédiatrie'),
        ('soins_continus', 'Soins continus'),
    ]

    hopital = models.ForeignKey(
        Hopital, on_delete=models.CASCADE, related_name='lits'
    )
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    total = models.IntegerField(default=0)
    occupes = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lit hôpital'
        verbose_name_plural = 'Lits hôpital'
        unique_together = ('hopital', 'service')

    def __str__(self):
        return f"{self.hopital.nom} — {self.get_service_display()} : {self.occupes}/{self.total}"

    @property
    def disponibles(self):
        return max(0, self.total - self.occupes)

    @property
    def taux_occupation(self):
        if self.total == 0:
            return 0.0
        return self.occupes / self.total
