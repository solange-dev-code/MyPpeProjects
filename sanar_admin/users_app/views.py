from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
import json

@login_required
def liste_users(request):
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

    # Données graphique 7 derniers jours
    from datetime import timedelta
    labels = []
    data_inscriptions = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        labels.append(day.strftime('%a'))
        data_inscriptions.append(
            User.objects.filter(date_joined__date=day).count()
        )

    context = {
        'users': users,
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
    }
    return render(request, 'users_app/liste.html', context)

@login_required
def ajouter_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff or is_superuser,
            is_superuser=is_superuser,
        )
        return redirect('users_app:liste')
    return render(request, 'users_app/ajouter.html')

@login_required
def modifier_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        user.save()
        return redirect('users_app:liste')
    return render(request, 'users_app/modifier.html', {'user': user})

@login_required
def supprimer_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST' and user != request.user:
        user.delete()
    return redirect('users_app:liste')