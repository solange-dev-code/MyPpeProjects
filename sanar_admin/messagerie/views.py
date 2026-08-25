from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Conversation, Message

@login_required
def liste_messages(request):
    conversations = Conversation.objects.all()
    non_lus = Message.objects.filter(lu=False).exclude(
        expediteur=request.user
    ).count()
    context = {
        'conversations': conversations,
        'non_lus': non_lus,
        'conversation_active': None,
    }
    return render(request, 'messagerie/liste.html', context)

@login_required
def conversation(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    conversations = Conversation.objects.all()
    msgs = conv.messages.all().order_by('created_at')
    msgs.filter(lu=False).exclude(
        expediteur=request.user
    ).update(lu=True)
    context = {
        'conversations': conversations,
        'conversation_active': conv,
        'msgs': msgs,
    }
    return render(request, 'messagerie/liste.html', context)

@login_required
def envoyer_message(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            Message.objects.create(
                conversation=conv,
                expediteur=request.user,
                contenu=contenu,
            )
    return redirect('messagerie:conversation', pk=pk)
@login_required
def nouvelle_conversation(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient')

        if not patient_id:
            from django.contrib import messages as msg
            msg.error(request, 'Veuillez sélectionner un patient.')
            from patients.models import Patient

            return render(request, 'messagerie/nouvelle.html', {
                'patients': Patient.objects.all()
            })

        from patients.models import Patient
        patient = get_object_or_404(Patient, pk=patient_id)

        conv, created = Conversation.objects.get_or_create(
            patient=patient,
            defaults={
                'nom': f"{patient.prenom} {patient.nom}",
                'type_contact': 'patient',
            }
        )

        if not conv.nom:
            conv.nom = f"{patient.prenom} {patient.nom}"
            conv.save()

        return redirect('messagerie:conversation', pk=conv.pk)

    from patients.models import Patient

    return render(request, 'messagerie/nouvelle.html', {
        'patients': Patient.objects.all()
    })