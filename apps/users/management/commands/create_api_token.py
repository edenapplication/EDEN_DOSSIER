# apps/users/management/commands/create_api_token.py

from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from apps.users.models import User


class Command(BaseCommand):
    help = 'Crée (ou recrée) le token API pour Laravel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default='api_laravel',
            help='Nom d\'utilisateur (défaut: api_laravel)'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime et recrée le token'
        )

    def handle(self, *args, **options):
        username = options['username']

        # ── Créer l'utilisateur API ──
        user, created = User.objects.get_or_create(
            username=username,
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
            self.stdout.write(self.style.SUCCESS(f"✅ Utilisateur '{username}' créé"))
        else:
            self.stdout.write(self.style.WARNING(f"ℹ️  Utilisateur '{username}' existait déjà"))

        # ── Reset si demandé ──
        if options['reset']:
            Token.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING("🗑️  Ancien token supprimé"))

        # ── Créer le token ──
        token, token_created = Token.objects.get_or_create(user=user)

        if token_created:
            self.stdout.write(self.style.SUCCESS("✅ Token créé"))
        else:
            self.stdout.write(self.style.WARNING("ℹ️  Token existant récupéré"))

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS(f"🔑 TOKEN : {token.key}"))
        self.stdout.write("=" * 60)
        self.stdout.write("")
        self.stdout.write("📋 Copiez ce token dans le .env de Laravel :")
        self.stdout.write(f"   DJANGO_API_TOKEN={token.key}")
        self.stdout.write("")