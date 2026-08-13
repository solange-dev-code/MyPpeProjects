"""Point d'entrée du package Sanar admin — importe Celery pour autodiscover."""
from .celery import app as celery_app

__all__ = ('celery_app',)
