from django.db import models
from django.contrib.auth.models import User
from hopitaux.models import Hopital

class Personnel(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrateur'),
        ('admin_hopital', 'Administrateur Hôpital'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personnel')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin_hopital')
    hopital = models.ForeignKey(
        Hopital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personnel'
    )
    telephone = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnel"
        ordering = ['-date_creation']