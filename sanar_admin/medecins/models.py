from django.db import models
from hopitaux.models import Hopital  # ← nouvel import

class Medecin(models.Model):
    SPECIALITE_CHOICES = [
        ('cardiologue', 'Cardiologue'),
        ('generaliste', 'Généraliste'),
        ('dermatologue', 'Dermatologue'),
        ('gynecologue', 'Gynécologue'),
        ('neurologue', 'Neurologue'),
        ('ophtalmologue', 'Ophtalmologue'),
        ('pediatre', 'Pédiatre'),
        ('radiologue', 'Radiologue'),
    ]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    specialite = models.CharField(max_length=50, choices=SPECIALITE_CHOICES)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    cabinet = models.CharField(max_length=200, blank=True)
    est_actif = models.BooleanField(default=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    hopital = models.ForeignKey(               # ← nouveau champ
        Hopital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medecins'
    )

    def __str__(self):
        return f"Dr. {self.prenom} {self.nom} - {self.get_specialite_display()}"

    class Meta:
        verbose_name = 'Médecin'
        ordering = ['nom']