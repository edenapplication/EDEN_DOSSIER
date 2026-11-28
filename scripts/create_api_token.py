# scripts/create_api_token.py
"""
Script pour créer (ou recréer) le token API pour Laravel.
Usage : python manage.py shell < scripts/create_api_token.py
   ou : python scripts/create_api_token.py  (avec DJANGO_SETTINGS_MODULE)
"""

import os
import django

# Configuration Django (si lancé directement avec python, pas manage.py shell)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# ⚠️ Adaptez 'config.settings' au nom réel de votre module settings
# (peut être 'EDEN_DOSSIER.settings', 'eden.settings', etc.)

django.setup()

from rest_framework.authtoken.models import Token
from apps.users.models import User

# ── Créer l'utilisateur API ──
user, created = User.objects.get_or_create(
    username='api_laravel',
    defaults={
        'role': 'admin',
        'is_staff': True,
        'last_name': 'API Laravel',
        'is_active': True,
    }
)

if created:
    user.set_password('UnMotDePasseTresSecurise2026!')
    user.save()
    print("✅ Utilisateur 'api_laravel' créé")
else:
    print("ℹ️  Utilisateur 'api_laravel' existait déjà")

# ── Créer (ou récupérer) le token ──
token, token_created = Token.objects.get_or_create(user=user)

if token_created:
    print("✅ Token créé")
else:
    print("ℹ️  Token existant récupéré")

print()
print("=" * 60)
print(f"🔑 TOKEN : {token.key}")
print("=" * 60)
print()
print("📋 Copiez ce token dans le .env de Laravel :")
print(f"   DJANGO_API_TOKEN={token.key}")
print()