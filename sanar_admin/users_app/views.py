"""
Vues users_app — gestion des utilisateurs par le super_admin.
- Le super_admin cree les admin_hopital et leur assigne un hopital.
- Le super_admin peut aussi gerer les autres comptes.
- Un admin_hopital ne peut pas creer d'utilisateurs.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
import json

from personnel.models import Personnel
from hopitaux.models import Hopital


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


@login_required
def liste_users(request):
    """Liste des utilisateurs — super_admin uniquement."""
    if not _est_super_admin(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    recherche = request.GET.get('q', '')
    role = request.GET.get('role', '')
    users = User.objects.all().order_by('-date_joined')

    if recherche:
        users = users.filter(
            Q(username__icontains=recherche) |
            Q(first_name__icontains=recherche) |
            Q(last_name__icontains=recherche) |
            Q(email__icontains=recherche)
        )
    if role == 'admin':
        users = users.filter(is_superuser=True)
    elif role == 'staff':
        users = users.filter(is_staff=True, is_superuser=False)
    elif role == 'user':
        users = users.filter(is_staff=False, is_superuser=False)

    total = User.objects.count()
    actifs = User.objects.filter(is_active=True).count()
    ce_mois = User.objects.filter(
        date_joined__month=timezone.now().month,
        date_joined__year=timezone.now().year,
    ).count()
    admins = User.objects.filter(is_superuser=True).count()
    staff = User.objects.filter(is_staff=True, is_superuser=False).count()
    simples = User.objects.filter(is_staff=False, is_superuser=False).count()

    # Donnees graphique 7 derniers jours
    from datetime import timedelta
    labels = []
    data_inscriptions = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        labels.append(day.strftime('%a'))
        data_inscriptions.append(
            User.objects.filter(date_joined__date=day).count()
        )

    # Recuperer les informations Personnel pour chaque user
    users_with_personnel = []
    for u in users:
        personnel = getattr(u, 'personnel', None)
        users_with_personnel.append({
            'user': u,
            'personnel': personnel,
            'role_display': personnel.get_role_display() if personnel else (
                'Super Admin' if u.is_superuser else ('Staff' if u.is_staff else 'Utilisateur')
            ),
            'hopital': personnel.hopital if personnel else None,
        })

    # Liste des hopitaux pour l'assignation
    hopitaux = Hopital.objects.filter(actif=True)

    context = {
        'users_with_personnel': users_with_personnel,
        'total': total,
        'actifs': actifs,
        'ce_mois': ce_mois,
        'admins': admins,
        'staff': staff,
        'simples': simples,
        'recherche': recherche,
        'role_filtre': role,
        'labels_json': json.dumps(labels),
        'data_json': json.dumps(data_inscriptions),
        'hopitaux': hopitaux,
    }
    return render(request, 'users_app/liste.html', context)


@login_required
def ajouter_user(request):
    """Creer un utilisateur + assigner un role et un hopital.
    - super_admin uniquement.
    - Cree un User + un Personnel (role + hopital).
    """
    if not _est_super_admin(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'admin_hopital')
        hopital_id = request.POST.get('hopital_id')

        # Verifier que le username n'existe pas deja
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Le nom d'utilisateur '{username}' existe deja.")
            return redirect('users_app:ajouter')

        # Verifier que le mot de passe est assez long
        if not password or len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caracteres.")
            hopitaux = Hopital.objects.filter(actif=True)
            return render(request, 'users_app/ajouter.html', {'hopitaux': hopitaux})

        # Creer le User
        try:
            is_superuser = (role == 'super_admin')
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=is_superuser,
            )
        except Exception as e:
            messages.error(request, f"Erreur lors de la creation : {e}")
            hopitaux = Hopital.objects.filter(actif=True)
            return render(request, 'users_app/ajouter.html', {'hopitaux': hopitaux})

        # Creer le Personnel avec role + hopital
        hopital = None
        if hopital_id and role == 'admin_hopital':
            try:
                hopital = Hopital.objects.get(pk=hopital_id, actif=True)
            except Hopital.DoesNotExist:
                messages.warning(request, "Hopital non trouve. Utilisateur cree sans hopital.")

        Personnel.objects.create(
            user=user,
            role=role,
            hopital=hopital,
            telephone=request.POST.get('telephone', ''),
        )

        messages.success(request,
            f"Utilisateur {username} cree avec succes. "
            f"Role : {dict(Personnel.ROLE_CHOICES).get(role, role)}"
            + (f" - Hopital : {hopital.nom}" if hopital else "")
        )
        return redirect('users_app:liste')

    hopitaux = Hopital.objects.filter(actif=True)
    context = {'hopitaux': hopitaux}
    return render(request, 'users_app/ajouter.html', context)


@login_required
def modifier_user(request, pk):
    """Modifier un utilisateur + son Personnel (role + hopital).
    - super_admin uniquement.
    """
    if not _est_super_admin(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.is_active = request.POST.get('is_active') == 'on'

        role = request.POST.get('role', 'admin_hopital')
        hopital_id = request.POST.get('hopital_id')

        user.is_superuser = (role == 'super_admin')
        user.is_staff = True
        user.save()

        # Mettre a jour ou creer le Personnel
        hopital = None
        if hopital_id and role == 'admin_hopital':
            try:
                hopital = Hopital.objects.get(pk=hopital_id, actif=True)
            except Hopital.DoesNotExist:
                pass

        personnel, created = Personnel.objects.update_or_create(
            user=user,
            defaults={
                'role': role,
                'hopital': hopital,
                'telephone': request.POST.get('telephone', ''),
            }
        )

        messages.success(request, f"Utilisateur {user.username} modifie avec succes.")
        return redirect('users_app:liste')

    # GET : afficher le formulaire
    personnel = getattr(user, 'personnel', None)
    hopitaux = Hopital.objects.filter(actif=True)
    context = {
        'user': user,
        'personnel': personnel,
        'hopitaux': hopitaux,
    }
    return render(request, 'users_app/modifier.html', context)


@login_required
def supprimer_user(request, pk):
    """Supprimer un utilisateur — super_admin uniquement."""
    if not _est_super_admin(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST' and user != request.user:
        # Supprimer aussi le Personnel lie (CASCADE le fait deja)
        user.delete()
        messages.success(request, f"Utilisateur {user.username} supprime.")
    return redirect('users_app:liste')
