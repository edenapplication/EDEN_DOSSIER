# apps/users/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.db import transaction
from apps.users.models import User
from apps.dossiers.models import Dossier, IntituleDossier, DossierAcces, DossierHistorique
import datetime


class PingView(APIView):
    """GET /api/ping/ — Test de connectivité (public)"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'Django API opérationnelle',
            'timestamp': timezone.now().isoformat(),
            'host': request.get_host(),
        })


class ImportClientsFromLaravelView(APIView):
    """POST /api/import/clients/ — Reçoit les clients depuis Laravel"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        clients_data = request.data.get('clients', [])
        if not clients_data:
            return Response({'error': 'Aucun client fourni'}, status=400)

        resultats = {
            'clients_created': 0,
            'clients_updated': 0,
            'dossiers_created': 0,
            'dossiers_skipped': 0,
            'errors': [],
            'imported_usernames': [],
        }

        for client_data in clients_data:
            try:
                username = client_data.get('username', '').strip()
                if not username:
                    continue

                # ── 1. Créer ou mettre à jour le User ──
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'last_name': client_data.get('nom', ''),
                        'email': client_data.get('email', ''),
                        'phone': client_data.get('phone', ''),
                        'city': client_data.get('city', 'Yaoundé'),
                        'sexe': client_data.get('sexe', 'masculin'),
                        'role': 'client',
                        'is_active': True,
                    }
                )
                if created:
                    user.set_password('eden')
                    user.save()
                    resultats['clients_created'] += 1
                else:
                    user.last_name = client_data.get('nom', user.last_name)
                    user.email = client_data.get('email', user.email)
                    user.phone = client_data.get('phone', user.phone)
                    user.save()
                    resultats['clients_updated'] += 1

                resultats['imported_usernames'].append(username)

                # ── 2. Créer les dossiers ──
                for dossier_data in client_data.get('dossiers', []):
                    intitule_name = dossier_data.get('intitule', '').strip()
                    if not intitule_name:
                        continue

                    intitule, _ = IntituleDossier.objects.get_or_create(
                        name=intitule_name
                    )

                    superficie = dossier_data.get('superficie')
                    date_paiement = None
                    date_raw = dossier_data.get('date_paiement')
                    if date_raw:
                        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                            try:
                                date_paiement = datetime.datetime.strptime(str(date_raw), fmt).date()
                                break
                            except ValueError:
                                continue

                    # Anti-doublon
                    existant = Dossier.objects.filter(
                        client=user,
                        intitule=intitule,
                        superficie=superficie,
                    ).first()

                    if existant:
                        resultats['dossiers_skipped'] += 1
                        continue

                    dossier = Dossier.objects.create(
                        client=user,
                        intitule=intitule,
                        superficie=superficie,
                        date_paiement=date_paiement,
                        description=dossier_data.get('notes', ''),
                    )
                    DossierAcces.objects.get_or_create(
                        dossier=dossier, user=user,
                        defaults={'est_proprietaire': True}
                    )
                    DossierHistorique.objects.create(
                        dossier=dossier,
                        message="Importé depuis Laravel via API"
                    )
                    resultats['dossiers_created'] += 1

            except Exception as e:
                resultats['errors'].append(f"Erreur {client_data.get('username')} : {str(e)}")

        return Response(resultats)


class ListeClientsDjangoView(APIView):
    """GET /api/clients/existants/ — Retourne tous les clients Django"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clients = User.objects.filter(role='client').prefetch_related('dossiers__intitule')

        data = []
        for user in clients:
            dossiers = [
                {
                    'reference': d.reference,
                    'intitule': d.intitule.name if d.intitule else '',
                    'superficie': float(d.superficie) if d.superficie else None,
                    'date_paiement': d.date_paiement.strftime('%Y-%m-%d') if d.date_paiement else None,
                    'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
                for d in user.dossiers.all()
            ]
            data.append({
                'username': user.username,
                'nom': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'sexe': user.sexe,
                'created_at': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'dossiers': dossiers,
            })

        return Response({
            'count': len(data),
            'clients': data,
        })