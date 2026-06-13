from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .decorators import admin_required
from apps.users.models import User
from apps.properties.models import Property, PropertyImage
from apps.promotions.models import Promotion
from apps.dossiers.models import Dossier, EtapeGlobale, EtapeCochee, DossierHistorique, IntituleDossier
from apps.reservations.models import Reservation
from apps.chatbot.models import ChatbotKnowledge, ChatbotUnknown
import csv
import datetime
import io


# ── DASHBOARD ──
@admin_required
def admin_dashboard(request):
    dossiers_alerte_list = Dossier.objects.filter(created_at__lte=timezone.now() - datetime.timedelta(days=45))
    dossiers_alerte = [d for d in dossiers_alerte_list if not d.is_complete()]
    ctx = {
        'total_clients': User.objects.filter(role='client').count(),
        'total_properties': Property.objects.count(),
        'total_dossiers': Dossier.objects.count(),
        'total_reservations': Reservation.objects.filter(status='pending').count(),
        'recent_reservations': Reservation.objects.order_by('-created_at')[:6],
        'recent_dossiers': Dossier.objects.select_related('client', 'intitule').order_by('-created_at')[:5],
        'unknown_questions': ChatbotUnknown.objects.count(),
        'alerte_45j_count': len(dossiers_alerte),
        'dossiers_alerte': dossiers_alerte[:3],
    }
    return render(request, 'adminpanel/dashboard.html', ctx)


# ── TERRAINS ──
@admin_required
def admin_properties(request):
    return render(request, 'adminpanel/properties/list.html', {'properties': Property.objects.prefetch_related('images').all()})


@admin_required
def admin_property_create(request):
    if request.method == 'POST':
        p = Property(title=request.POST.get('title'), description=request.POST.get('description'), location=request.POST.get('location'), area=request.POST.get('area'), price=request.POST.get('price'), is_active=request.POST.get('is_active') == 'on', is_featured=request.POST.get('is_featured') == 'on')
        if request.FILES.get('main_image'):
            p.main_image = request.FILES['main_image']
        p.save()
        for img in request.FILES.getlist('gallery_images'):
            PropertyImage.objects.create(property=p, image=img)
        messages.success(request, "Terrain créé.")
        return redirect('admin_properties')
    return render(request, 'adminpanel/properties/form.html', {'action': 'Créer'})


@admin_required
def admin_property_edit(request, pk):
    p = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        p.title = request.POST.get('title')
        p.description = request.POST.get('description')
        p.location = request.POST.get('location')
        p.area = request.POST.get('area')
        p.price = request.POST.get('price')
        p.is_active = request.POST.get('is_active') == 'on'
        p.is_featured = request.POST.get('is_featured') == 'on'
        if request.FILES.get('main_image'):
            p.main_image = request.FILES['main_image']
        p.save()
        for img in request.FILES.getlist('gallery_images'):
            PropertyImage.objects.create(property=p, image=img)
        messages.success(request, "Terrain modifié.")
        return redirect('admin_properties')
    return render(request, 'adminpanel/properties/form.html', {'property': p, 'action': 'Modifier'})


@admin_required
def admin_property_delete(request, pk):
    p = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        p.delete()
        messages.success(request, "Terrain supprimé.")
    return redirect('admin_properties')


# ── PROMOTIONS ──
@admin_required
def admin_promotions(request):
    return render(request, 'adminpanel/promotions/list.html', {'promotions': Promotion.objects.all()})


@admin_required
def admin_promotion_create(request):
    if request.method == 'POST':
        pr = Promotion(title=request.POST.get('title'), subtitle=request.POST.get('subtitle', ''), description=request.POST.get('description'), badge=request.POST.get('badge', ''), badge_color=request.POST.get('badge_color', '#C1121F'), price=request.POST.get('price') or None, location=request.POST.get('location', ''), advantages=request.POST.get('advantages', ''), conditions=request.POST.get('conditions', ''), order=int(request.POST.get('order', 0)), is_active=request.POST.get('is_active') == 'on')
        if request.FILES.get('image'):
            pr.image = request.FILES['image']
        pr.save()
        messages.success(request, "Promotion créée.")
        return redirect('admin_promotions')
    return render(request, 'adminpanel/promotions/form.html', {'action': 'Créer'})


@admin_required
def admin_promotion_edit(request, pk):
    pr = get_object_or_404(Promotion, pk=pk)
    if request.method == 'POST':
        pr.title = request.POST.get('title')
        pr.subtitle = request.POST.get('subtitle', '')
        pr.description = request.POST.get('description')
        pr.badge = request.POST.get('badge', '')
        pr.badge_color = request.POST.get('badge_color', '#C1121F')
        pr.price = request.POST.get('price') or None
        pr.location = request.POST.get('location', '')
        pr.advantages = request.POST.get('advantages', '')
        pr.conditions = request.POST.get('conditions', '')
        pr.order = int(request.POST.get('order', 0))
        pr.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('image'):
            pr.image = request.FILES['image']
        pr.save()
        messages.success(request, "Promotion modifiée.")
        return redirect('admin_promotions')
    return render(request, 'adminpanel/promotions/form.html', {'promotion': pr, 'action': 'Modifier'})


@admin_required
def admin_promotion_delete(request, pk):
    pr = get_object_or_404(Promotion, pk=pk)
    if request.method == 'POST':
        pr.delete()
        messages.success(request, "Promotion supprimée.")
    return redirect('admin_promotions')


# ── INTITULÉS ──
@admin_required
def admin_intitules(request):
    intitules = IntituleDossier.objects.all()
    return render(request, 'adminpanel/intitules/list.html', {'intitules': intitules})


@admin_required
def admin_intitule_create(request):
    if request.method == 'POST':
        IntituleDossier.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', '')
        )
        messages.success(request, "Intitulé créé.")
        return redirect('admin_intitules')
    return render(request, 'adminpanel/intitules/form.html', {'action': 'Créer'})


@admin_required
def admin_intitule_edit(request, pk):
    obj = get_object_or_404(IntituleDossier, pk=pk)
    if request.method == 'POST':
        obj.name = request.POST.get('name')
        obj.description = request.POST.get('description', '')
        obj.save()
        messages.success(request, "Intitulé modifié.")
        return redirect('admin_intitules')
    return render(request, 'adminpanel/intitules/form.html', {'intitule': obj, 'action': 'Modifier'})


@admin_required
def admin_intitule_delete(request, pk):
    obj = get_object_or_404(IntituleDossier, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Intitulé supprimé.")
    return redirect('admin_intitules')


# ── CLIENTS / UTILISATEURS ──
@admin_required
def admin_clients(request):
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('-date_joined')
    if role_filter:
        users = users.filter(role=role_filter)
    return render(request, 'adminpanel/clients/list.html', {
        'clients': users,
        'role_filter': role_filter,
        'roles': User.ROLE_CHOICES,
    })


@admin_required
def admin_client_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'client')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Cet identifiant existe déjà.")
            return render(request, 'adminpanel/clients/form.html', {'action': 'Créer', 'roles': User.ROLE_CHOICES})
        u = User.objects.create_user(
            username=username,
            password=password,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            city=request.POST.get('city', ''),
            role=role,
            sexe=request.POST.get('sexe', 'masculin'),
        )
        if role in ('admin', 'commercial'):
            u.is_staff = True
            u.save()
        messages.success(request, f"Utilisateur créé — Identifiant : {username} | Mot de passe : {password}")
        return redirect('admin_clients')
    return render(request, 'adminpanel/clients/form.html', {'action': 'Créer', 'roles': User.ROLE_CHOICES})


@admin_required
def admin_client_edit(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        u.first_name = request.POST.get('first_name', '')
        u.last_name = request.POST.get('last_name', '')
        u.email = request.POST.get('email', '')
        u.phone = request.POST.get('phone', '')
        u.city = request.POST.get('city', '')
        u.is_active = request.POST.get('is_active') == 'on'
        u.sexe = request.POST.get('sexe', 'masculin')
        new_role = request.POST.get('role', u.role)
        u.role = new_role
        u.is_staff = new_role in ('admin', 'commercial')
        if request.POST.get('password'):
            u.set_password(request.POST.get('password'))
        u.save()
        messages.success(request, "Utilisateur modifié.")
        return redirect('admin_clients')
    return render(request, 'adminpanel/clients/form.html', {'client': u, 'action': 'Modifier', 'roles': User.ROLE_CHOICES})

@admin_required
def admin_client_delete(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        u.delete()
        messages.success(request, "Utilisateur supprimé.")
    return redirect('admin_clients')


@admin_required
def admin_clients_export(request):
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('role', 'last_name')
    if role_filter:
        users = users.filter(role=role_filter)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="utilisateurs_eden.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Identifiant', 'Prénom', 'Nom', 'Email', 'Téléphone', 'Ville', 'Rôle', 'Actif', 'Date inscription'])
    for u in users:
        writer.writerow([u.username, u.first_name, u.last_name, u.email, u.phone, u.city, u.get_role_display(), 'Oui' if u.is_active else 'Non', u.date_joined.strftime('%d/%m/%Y')])
    return response


@admin_required
def admin_clients_import(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded), delimiter=';')
        created = 0
        errors = []
        for i, row in enumerate(reader, 2):
            username = row.get('Identifiant', '').strip()
            password = row.get('Mot de passe', '').strip()
            role = row.get('Rôle', 'client').strip().lower()
            if not username or not password:
                errors.append(f"Ligne {i} : identifiant ou mot de passe manquant")
                continue
            if User.objects.filter(username=username).exists():
                errors.append(f"Ligne {i} : {username} existe déjà")
                continue
            role_map = {'administrateur': 'admin', 'commercial': 'commercial', 'client': 'client', 'admin': 'admin'}
            role_val = role_map.get(role, 'client')
            u = User.objects.create_user(
                username=username, password=password,
                first_name=row.get('Prénom', '').strip(),
                last_name=row.get('Nom', '').strip(),
                email=row.get('Email', '').strip(),
                phone=row.get('Téléphone', '').strip(),
                city=row.get('Ville', '').strip(),
                role=role_val,
            )
            if role_val == 'admin':
                u.is_staff = True
                u.save()
            created += 1
        msg = f"{created} utilisateur(s) importé(s)."
        if errors:
            msg += f" {len(errors)} erreur(s) : " + " | ".join(errors[:5])
        messages.success(request, msg)
        return redirect('admin_clients')
    return render(request, 'adminpanel/clients/import.html')


@admin_required
def admin_clients_template(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="modele_import_utilisateurs.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Identifiant', 'Mot de passe', 'Prénom', 'Nom', 'Email', 'Téléphone', 'Ville', 'Rôle'])
    writer.writerow(['jean.dupont', 'motdepasse123', 'Jean', 'Dupont', 'jean@email.com', '+237600000000', 'Yaoundé', 'client'])
    writer.writerow(['marie.martin', 'motdepasse456', 'Marie', 'Martin', 'marie@email.com', '+237600000001', 'Douala', 'commercial'])
    return response


# ── ÉTAPES ──
@admin_required
def admin_etapes_globales(request):
    etapes_tech = EtapeGlobale.objects.filter(type='technique')
    etapes_morc = EtapeGlobale.objects.filter(type='morcellement')
    return render(request, 'adminpanel/etapes/list.html', {'etapes_tech': etapes_tech, 'etapes_morc': etapes_morc, 'total_tech': sum(e.percentage for e in etapes_tech), 'total_morc': sum(e.percentage for e in etapes_morc)})


@admin_required
def admin_etape_globale_create(request):
    if request.method == 'POST':
        type_ = request.POST.get('type')
        pct = int(request.POST.get('percentage', 0))
        total_actuel = sum(e.percentage for e in EtapeGlobale.objects.filter(type=type_))
        if total_actuel + pct > 100:
            messages.error(request, f"Impossible : total dépasserait 100% (actuel : {total_actuel}%)")
            return redirect('admin_etapes_globales')
        EtapeGlobale.objects.create(name=request.POST.get('name'), type=type_, percentage=pct, order=int(request.POST.get('order', 0)), description=request.POST.get('description', ''))
        messages.success(request, "Étape créée.")
        return redirect('admin_etapes_globales')
    return render(request, 'adminpanel/etapes/form.html', {'action': 'Créer'})


@admin_required
def admin_etape_globale_edit(request, pk):
    etape = get_object_or_404(EtapeGlobale, pk=pk)
    if request.method == 'POST':
        pct = int(request.POST.get('percentage', 0))
        total_actuel = sum(e.percentage for e in EtapeGlobale.objects.filter(type=etape.type).exclude(pk=pk))
        if total_actuel + pct > 100:
            messages.error(request, f"Impossible : total dépasserait 100%")
            return redirect('admin_etapes_globales')
        etape.name = request.POST.get('name')
        etape.percentage = pct
        etape.order = int(request.POST.get('order', 0))
        etape.description = request.POST.get('description', '')
        etape.save()
        messages.success(request, "Étape modifiée.")
        return redirect('admin_etapes_globales')
    return render(request, 'adminpanel/etapes/form.html', {'etape': etape, 'action': 'Modifier'})


@admin_required
def admin_etape_globale_delete(request, pk):
    etape = get_object_or_404(EtapeGlobale, pk=pk)
    if request.method == 'POST':
        etape.delete()
        messages.success(request, "Étape supprimée.")
    return redirect('admin_etapes_globales')


# ── DOSSIERS ──
@admin_required
def admin_dossiers(request):
    dossiers = Dossier.objects.select_related('client', 'intitule').all()
    dossiers_data = [{'dossier': d, 'is_complete': d.is_complete()} for d in dossiers]
    return render(request, 'adminpanel/dossiers/list.html', {'dossiers_data': dossiers_data})


@admin_required
def admin_dossier_create(request):
    clients = User.objects.filter(role='client', is_active=True)
    intitules = IntituleDossier.objects.all()
    if request.method == 'POST':
        client = get_object_or_404(User, pk=request.POST.get('client'), role='client')
        intitule_id = request.POST.get('intitule')
        intitule = get_object_or_404(IntituleDossier, pk=intitule_id) if intitule_id else None
        d = Dossier(
            client=client,
            intitule=intitule,
            description=request.POST.get('description', ''),
            superficie=request.POST.get('superficie') or None,
            date_paiement=request.POST.get('date_paiement') or None,
        )
        if request.FILES.get('photo'):
            d.photo = request.FILES['photo']
        d.save()
        d.planifier_cochages_automatiques()
        DossierHistorique.objects.create(dossier=d, message="Dossier créé — cochage automatique planifié", created_by=request.user)
        messages.success(request, f"Dossier {d.reference} créé.")
        return redirect('admin_dossier_detail', pk=d.pk)
    return render(request, 'adminpanel/dossiers/form.html', {'clients': clients, 'intitules': intitules, 'action': 'Créer'})


@admin_required
def admin_dossier_detail(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk)
    dossier.appliquer_cochages_automatiques()
    etapes_tech = dossier.get_etapes_technique()
    etapes_morc = dossier.get_etapes_morcellement()
    historique = dossier.historique.all()[:30]
    prog_tech = dossier.get_progression_technique()
    prog_morc = dossier.get_progression_morcellement()
    total_tech = dossier.get_total_technique()
    total_morc = dossier.get_total_morcellement()
    pct_tech_bar = round(prog_tech / total_tech * 100) if total_tech > 0 else 0
    pct_morc_bar = round(prog_morc / total_morc * 100) if total_morc > 0 else 0
    etapes_tech_list = list(EtapeGlobale.objects.filter(type='technique'))
    etapes_morc_list = list(EtapeGlobale.objects.filter(type='morcellement'))
    return render(request, 'adminpanel/dossiers/detail.html', {
        'dossier': dossier,
        'etapes_tech': etapes_tech,
        'etapes_morc': etapes_morc,
        'historique': historique,
        'prog_tech': prog_tech,
        'prog_morc': prog_morc,
        'total_tech': total_tech,
        'total_morc': total_morc,
        'pct_tech_bar': pct_tech_bar,
        'pct_morc_bar': pct_morc_bar,
        'current_tech': dossier.get_current_etape_technique(),
        'current_morc': dossier.get_current_etape_morcellement(),
        'morc_locked': not dossier.is_technique_complete(),
        'last_tech_id': etapes_tech_list[-1].pk if etapes_tech_list else None,
        'last_morc_id': etapes_morc_list[-1].pk if etapes_morc_list else None,
    })


@admin_required
@require_POST
def admin_etape_toggle(request, dossier_pk, etape_pk):
    dossier = get_object_or_404(Dossier, pk=dossier_pk)
    etape = get_object_or_404(EtapeGlobale, pk=etape_pk)
    if etape.type == 'morcellement' and not dossier.is_technique_complete():
        return JsonResponse({'status': 'error', 'message': 'Le technique doit être à 100% d\'abord.'}, status=403)
    cochee, _ = EtapeCochee.objects.get_or_create(dossier=dossier, etape=etape)
    cochee.is_done = not cochee.is_done
    cochee.done_at = timezone.now() if cochee.is_done else None
    cochee.done_by = request.user if cochee.is_done else None
    if not cochee.is_done:
        cochee.done_by = None
    cochee.save()
    action = "validée manuellement" if cochee.is_done else "annulée"
    prog = dossier.get_progression_technique() if etape.type == 'technique' else dossier.get_progression_morcellement()
    total = dossier.get_total_technique() if etape.type == 'technique' else dossier.get_total_morcellement()
    DossierHistorique.objects.create(dossier=dossier, message=f"Étape '{etape.name}' {action} — {etape.get_type_display()} : {prog}%", created_by=request.user)
    pct_bar = round(prog / total * 100) if total > 0 else 0
    current = dossier.get_current_etape_technique() if etape.type == 'technique' else dossier.get_current_etape_morcellement()
    return JsonResponse({'status': 'ok', 'is_done': cochee.is_done, 'progression': prog, 'pct_bar': pct_bar, 'type': etape.type, 'morc_unlocked': dossier.is_technique_complete(), 'current_etape_name': current.name if current else '', 'current_etape_desc': current.description if current else ''})


@admin_required
def admin_dossier_delete(request, pk):
    d = get_object_or_404(Dossier, pk=pk)
    if request.method == 'POST':
        d.delete()
        messages.success(request, "Dossier supprimé.")
    return redirect('admin_dossiers')


@admin_required
def admin_dossiers_alerte(request):
    seuil = timezone.now() - datetime.timedelta(days=45)
    tous = Dossier.objects.filter(created_at__lte=seuil).select_related('client', 'intitule')
    dossiers = [d for d in tous if not d.is_complete()]
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="dossiers_alerte_45j.csv"'
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Référence', 'Intitulé', 'Client', 'Téléphone', 'Email', 'Superficie', 'Date paiement', 'Jours', 'Tech %', 'Morc %'])
        for d in dossiers:
            writer.writerow([d.reference, d.get_title(), d.client.get_full_name() or d.client.username, d.client.phone, d.client.email, d.superficie or '', d.date_paiement.strftime('%d/%m/%Y') if d.date_paiement else '', d.get_jours_existence(), d.get_progression_technique(), d.get_progression_morcellement()])
        return response
    return render(request, 'adminpanel/dossiers/alerte.html', {'dossiers': dossiers, 'count': len(dossiers)})


# ── RÉSERVATIONS ──
@admin_required
def admin_reservations(request):
    return render(request, 'adminpanel/reservations/list.html', {'reservations': Reservation.objects.select_related('property_link', 'promotion_link').all()})


@admin_required
def admin_reservation_update(request, pk):
    r = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        r.status = request.POST.get('status', r.status)
        r.save()
        messages.success(request, "Statut mis à jour.")
    return redirect('admin_reservations')


# ── CHATBOT ──
@admin_required
def admin_chatbot(request):
    return render(request, 'adminpanel/chatbot/list.html', {'knowledges': ChatbotKnowledge.objects.all(), 'unknowns': ChatbotUnknown.objects.all()[:50]})


@admin_required
def admin_chatbot_create(request):
    if request.method == 'POST':
        ChatbotKnowledge.objects.create(keywords=request.POST.get('keywords'), question_example=request.POST.get('question_example'), answer=request.POST.get('answer'), order=int(request.POST.get('order', 0)), is_active=request.POST.get('is_active') == 'on')
        messages.success(request, "Réponse ajoutée.")
        return redirect('admin_chatbot')
    return render(request, 'adminpanel/chatbot/form.html', {'action': 'Ajouter'})


@admin_required
def admin_chatbot_edit(request, pk):
    kb = get_object_or_404(ChatbotKnowledge, pk=pk)
    if request.method == 'POST':
        kb.keywords = request.POST.get('keywords')
        kb.question_example = request.POST.get('question_example')
        kb.answer = request.POST.get('answer')
        kb.order = int(request.POST.get('order', 0))
        kb.is_active = request.POST.get('is_active') == 'on'
        kb.save()
        messages.success(request, "Réponse modifiée.")
        return redirect('admin_chatbot')
    return render(request, 'adminpanel/chatbot/form.html', {'kb': kb, 'action': 'Modifier'})


@admin_required
def admin_chatbot_delete(request, pk):
    kb = get_object_or_404(ChatbotKnowledge, pk=pk)
    if request.method == 'POST':
        kb.delete()
        messages.success(request, "Supprimé.")
    return redirect('admin_chatbot')