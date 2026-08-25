from django.db import models
from hopitaux.models import Hopital


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
        # Nouvelles spécialités (phase 2)
        ('anesthesiste', 'Anesthésiste'),
        ('chirurgien', 'Chirurgien'),
        ('urgentiste', 'Urgentiste'),
        ('psychiatre', 'Psychiatre'),
        ('endocrinologue', 'Endocrinologue'),
        ('gastro_enterologue', 'Gastro-entérologue'),
        ('pneumologue', 'Pneumologue'),
        ('rhumatologue', 'Rhumatologue'),
        ('urologue', 'Urologue'),
        ('ORL', 'ORL'),
    ]

    user = models.OneToOneField(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medecin_profile',
        help_text="Lien vers le compte Django (pour login + 2FA)"
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    specialite = models.CharField(max_length=50, choices=SPECIALITE_CHOICES)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    cabinet = models.CharField(max_length=200, blank=True)
    est_actif = models.BooleanField(default=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    hopital = models.ForeignKey(
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


class DisponibiliteMedecin(models.Model):
    """Plage horaire récurrente de disponibilité d'un médecin.

    Ex : « Dr. Dupont consulte le mardi matin 9h-12h à l'hôpital X, créneaux de 30 min »
    Le service creneaux_disponibles() génère la liste des créneaux réservables
    pour une date donnée à partir de ce modèle.
    """

    JOURS_SEMAINE = [
        (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'),
        (3, 'Jeudi'),  (4, 'Vendredi'), (5, 'Samedi'),
        (6, 'Dimanche'),
    ]

    medecin = models.ForeignKey(
        Medecin, on_delete=models.CASCADE, related_name='disponibilites'
    )
    hopital = models.ForeignKey(
        Hopital, on_delete=models.CASCADE, related_name='disponibilites'
    )
    jour_semaine = models.IntegerField(choices=JOURS_SEMAINE)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    duree_creneau = models.IntegerField(
        default=30, help_text="Durée d'un créneau en minutes"
    )
    actif = models.BooleanField(default=True)
    validite_depuis = models.DateField()
    validite_jusqua = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Disponibilité médecin'
        verbose_name_plural = 'Disponibilités médecin'
        ordering = ['medecin', 'jour_semaine', 'heure_debut']

    def __str__(self):
        return f"{self.medecin} — {self.get_jour_semaine_display()} {self.heure_debut}-{self.heure_fin}"


class CongeMedecin(models.Model):
    """Période de congé d'un médecin (exclut les créneaux générés)."""

    medecin = models.ForeignKey(
        Medecin, on_delete=models.CASCADE, related_name='conges'
    )
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        verbose_name = 'Congé médecin'
        verbose_name_plural = 'Congés médecin'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.medecin} — {self.date_debut} → {self.date_fin}"

    def couvre(self, date_cible):
        """Retourne True si le congé couvre la date cible."""
        return self.date_debut <= date_cible <= self.date_fin


class GoogleCalendarLink(models.Model):
    """Lien OAuth2 entre un médecin et son Google Calendar.

    Permet la synchronisation bidirectionnelle des rendez-vous.
    """

    medecin = models.OneToOneField(
        Medecin, on_delete=models.CASCADE, related_name='google_calendar'
    )
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    calendar_id = models.CharField(max_length=200, default='primary')
    sync_actif = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lien Google Calendar'
        verbose_name_plural = 'Liens Google Calendar'

    def __str__(self):
        return f"Google Calendar — {self.medecin}"

    @property
    def token_valide(self):
        """True si le token est encore valide."""
        if not self.token_expiry:
            return False
        from django.utils import timezone
        return self.token_expiry > timezone.now()
