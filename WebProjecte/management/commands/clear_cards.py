from django.core.management.base import BaseCommand
from WebProjecte.models import Card, Rarity, CardSet, CollectionCard

class Command(BaseCommand):
    help = 'Borra todas las cartas, rarezas, colecciones...'

    def handle(self, *args, **kwargs):
        CollectionCard.objects.all().delete()
        Card.objects.all().delete()
        CardSet.objects.all().delete()
        Rarity.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("🧹 Datos reseteados."))
