from django.core.management.base import BaseCommand
from WebProjecte.models import Card, Rarity, CardSet

class Command(BaseCommand):
    help = 'Sembrar la base de datos con cartas de ejemplo'

    def handle(self, *args, **kwargs):
        # Crear o recuperar rareza
        rareza, _ = Rarity.objects.get_or_create(
            title="Legendaria",
            defaults={
                'description': 'Cartas muy difíciles de conseguir',
                'probability': 0.05
            }
        )

        # Crear o recuperar set
        set_inicial, _ = CardSet.objects.get_or_create(
            title="Set Inicial",
            defaults={
                'description': 'Primera colección de cartas',
                'image_url': 'https://example.com/set-inicial.jpg'
            }
        )

        # Lista de cartas a añadir
        cartas = [
            {
                "title": "Gimeno",
                "description": "Devuelve tus cartas de cuarto curso a primer curso.",
                "image_url": "https://inkscape.app/wp-content/uploads/imagen-vectorial.webp",
            },
            {
                "title": "Torres",
                "description": "Te obliga a reescribir tu TFG cada semana.",
                "image_url": "https://example.com/torres.jpg",
            },
            {
                "title": "Martínez",
                "description": "Cuando entra al campo, todos los estudiantes se duermen.",
                "image_url": "https://example.com/martinez.jpg",
            },
            {
                "title": "Bestia del Lab",
                "description": "Una criatura legendaria con hambre de proyectos.",
                "image_url": "https://example.com/bestia.jpg",
            }
        ]

        # Crear cartas
        for carta_data in cartas:
            card, created = Card.objects.get_or_create(
                title=carta_data["title"],
                defaults={
                    "description": carta_data["description"],
                    "image_url": carta_data["image_url"],
                    "rarity": rareza,
                    "card_set": set_inicial
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Carta '{card.title}' creada"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Carta '{card.title}' ya existía"))
