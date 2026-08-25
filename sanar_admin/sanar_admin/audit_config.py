"""
Configuration centralisée de l'audit trail avec django-auditlog.

Enregistre automatiquement les create/update/delete sur les modèles
sensibles pour conformité RGPD. Pour journaliser les accès en lecture
(consultation de dossier), utiliser le décorateur @log_action.

Usage :
    from auditlog.registry import auditlog
    auditlog.register(Patient)
"""
from auditlog.registry import auditlog

# ─── Modèles sensibles à journaliser automatiquement (create/update/delete) ───
from patients.models import Patient
from dossiers_medicaux.models import DossierMedical, Prescription, Document
from analyses.models import Analyse, ResultatAnalyse
from appointments.models import RendezVous
from consultations.models import Consultation
from facturation.models import Facture
from urgences.models import DemandeUrgence

# Enregistrement (idempotent — auditlog gère les doublons)
_audit_models = [
    Patient, DossierMedical, Prescription, Document,
    Analyse, ResultatAnalyse,
    RendezVous, Consultation, Facture,
    DemandeUrgence,
]

for _model in _audit_models:
    try:
        auditlog.register(_model)
    except Exception:
        # déjà enregistré
        pass


def journaliser_acces_lecture(user, objet, action_label='view'):
    """Journalise manuellement un accès en lecture.

    django-auditlog ne journalise que les écritures par défaut.
    Pour les accès en lecture (consultation de dossier sensible),
    appeler cette fonction explicitement.

    Usage :
        from sanar_admin.audit_config import journaliser_accre_lecture
        journaliser_acces_lecture(request.user, dossier, 'consultation_dossier')
    """
    from auditlog.models import LogEntry
    try:
        LogEntry.objects.log_create(
            instance=objet,
            action=LogEntry.Action.ACCESS,
            changes={action_label: 'access'},
            actor=user,
        )
    except Exception:
        # Si l'action ACCESS n'existe pas dans cette version, fallback
        try:
            LogEntry.objects.log_create(
                instance=objet,
                action=LogEntry.Action.UPDATE,
                changes={action_label: 'read_access'},
                actor=user,
            )
        except Exception:
            pass
