"""
Management command : anonymise les patients inactifs depuis > X mois.

RGPD — article 17 : droit à l'oubli. Cette commande permet au DPO de
nettoyer périodiquement les comptes inactifs en anonymisant leurs données.

Usage :
    python manage.py anonymiser_inactifs --mois=24
    python manage.py anonymiser_inactifs --mois=12 --dry-run
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth.models import User
from patients.models import Patient
from dossiers_medicaux.models import DossierMedical
from api.models import DeviceToken

logger = logging.getLogger('sanar.management')


class Command(BaseCommand):
    help = 'Anonymise les patients inactifs depuis plus de X mois (RGPD art. 17)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mois',
            type=int,
            default=24,
            help='Nombre de mois d\'inactivité avant anonymisation (défaut: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les patients qui seraient anonymisés sans les modifier'
        )

    def handle(self, *args, **options):
        mois = options['mois']
        dry_run = options['dry_run']
        seuil = timezone.now() - timedelta(days=mois * 30)

        # Patients dont le user ne s'est pas connecté depuis `mois`
        # (last_login null = jamais connecté → on saute si inscription < seuil)
        users_inactifs = User.objects.filter(
            is_active=True,
            last_login__lt=seuil,
        ).exclude(last_login=None)

        patients_a_anonymiser = Patient.objects.filter(
            user__in=users_inactifs
        )

        count = patients_a_anonymiser.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                f'Aucun patient inactif depuis {mois} mois.'
            ))
            return

        self.stdout.write(self.style.WARNING(
            f'{count} patient(s) inactif(s) depuis {mois} mois trouvé(s).'
        ))

        if dry_run:
            self.stdout.write('Mode DRY-RUN — aucune modification effectuée.')
            for p in patients_a_anonymiser[:20]:
                self.stdout.write(f'  - {p.patient_id} : {p.prenom} {p.nom} '
                                  f'(user: {p.user.username}, last login: {p.user.last_login})')
            if count > 20:
                self.stdout.write(f'  ... et {count - 20} autres')
            return

        if not dry_run:
            confirm = input(
                f'\nConfirmer l\'anonymisation IRRÉVERSIBLE de {count} patient(s) ? '
                f'Tapez "OUI" pour confirmer : '
            )
            if confirm != 'OUI':
                self.stdout.write(self.style.ERROR('Annulé.'))
                return

        anonymised = 0
        for patient in patients_a_anonymiser:
            try:
                # Anonymiser Patient
                patient.nom = 'ANONYMISE'
                patient.prenom = 'ANONYMISE'
                patient.email = f'anonymise_{patient.id}@deleted.local'
                patient.telephone = '0000000000'
                patient.adresse = 'ANONYMISE'
                patient.allergies = ''
                patient.urgence_qr_actif = False
                patient.regenerer_token_urgence()
                patient.save()

                # Supprimer DeviceTokens
                DeviceToken.objects.filter(user=patient.user).delete()

                # Supprimer DossierMedical + prescriptions + documents
                try:
                    dossier = patient.dossiermedical
                    dossier.prescriptions.all().delete()
                    dossier.documents.all().delete()
                    dossier.delete()
                except DossierMedical.DoesNotExist:
                    pass

                # Désactiver user
                user = patient.user
                user.is_active = False
                user.email = f'anonymise_{patient.id}@deleted.local'
                user.first_name = 'ANONYMISE'
                user.last_name = 'ANONYMISE'
                user.save()

                anonymised += 1
                logger.info("Patient %s anonymisé (user %s)", patient.id, user.id)
            except Exception as e:
                logger.error("Échec anonymisation patient %s : %s", patient.id, e)

        self.stdout.write(self.style.SUCCESS(
            f'{anonymised}/{count} patient(s) anonymisé(s) avec succès.'
        ))
