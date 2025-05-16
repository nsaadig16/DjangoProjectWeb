from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Deletes all users except superusers'

    def handle(self, *args, **kwargs):
        users_deleted = User.objects.exclude(is_superuser=True).delete()
        self.stdout.write(self.style.SUCCESS(f"🧹 Deleted {users_deleted[0]} users (excluding superusers)."))
