from django.core.management.base import BaseCommand
from WebProjecte.models import Rarity

class Command(BaseCommand):
    help = 'Sembrar la base de datos con rarezas iniciales'

    def handle(self, *args, **kwargs):
        rarezas = [
            {
                "title": "Común",
                "description": "Fácil de conseguir.",
                "probability": 0.6
            },
            {
                "title": "Poco Común",
                "description": "Un poco más difícil de conseguir.",
                "probability": 0.25
            },
            {
                "title": "Rara",
                "description": "Difícil de conseguir.",
                "probability": 0.1
            },
            {
                "title": "Legendaria",
                "description": "Extremadamente difícil de conseguir.",
                "probability": 0.05
            }
        ]

        for data in rarezas:
            rarity, created = Rarity.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "probability": data["probability"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Rareza '{rarity.title}' creada"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Rareza '{rarity.title}' ya existía"))
