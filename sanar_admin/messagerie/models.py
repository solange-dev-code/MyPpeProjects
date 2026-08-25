from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient

class Conversation(models.Model):
    TYPE_CHOICES = [
        ('patient', 'Patient'),
        ('medecin', 'Médecin'),
        ('equipe', 'Équipe'),
        ('vendor', 'Vendeur'),
    ]

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, null=True, blank=True
    )
    participants = models.ManyToManyField(User, related_name='conversations')
    nom = models.CharField(max_length=100, default='', blank=True)
    type_contact = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='patient'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation - {self.nom}"

    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.expediteur} - {self.created_at}"

    class Meta:
        ordering = ['created_at']