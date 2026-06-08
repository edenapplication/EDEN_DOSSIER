from django.core.management.base import BaseCommand
from apps.users.models import User


class Command(BaseCommand):
    help = 'Crée un utilisateur admin et un utilisateur client par défaut'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                password='admin1234',
                email='admin@edengroup.cm',
                first_name='Admin',
                last_name='Eden',
                role='admin',
            )
            self.stdout.write(self.style.SUCCESS('✓ Admin créé — login: admin / mdp: admin1234'))
        else:
            self.stdout.write('Admin existe déjà')

        if not User.objects.filter(username='client').exists():
            User.objects.create_user(
                username='client',
                password='client1234',
                email='client@edengroup.cm',
                first_name='Jean',
                last_name='Mballa',
                role='client',
            )
            self.stdout.write(self.style.SUCCESS('✓ Client créé — login: client / mdp: client1234'))
        else:
            self.stdout.write('Client existe déjà')