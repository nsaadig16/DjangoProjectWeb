from django.core.management.base import BaseCommand
from WebProjecte.models import Rarity

class Command(BaseCommand):
    help = 'Seed the database with initial rarities'

    def handle(self, *args, **kwargs):
        rarities = [
            {
                "title": "Common",
                "description": "Easy to get.",
                "probability": 0.6
            },
            {
                "title": "Rare",
                "description": "A little harder to get.",
                "probability": 0.25
            },
            {
                "title": "Epic",
                "description": "Hard to get.",
                "probability": 0.1
            },
            {
                "title": "Legendary",
                "description": "Extremely hard to get.",
                "probability": 0.05
            }
        ]

        for data in rarities:
            rarity, created = Rarity.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "probability": data["probability"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Rarity '{rarity.title}' created"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Rarity '{rarity.title}' already exists"))
