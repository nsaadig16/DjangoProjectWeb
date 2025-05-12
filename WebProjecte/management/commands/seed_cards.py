from django.core.management.base import BaseCommand
from WebProjecte.models import Card, Rarity, CardSet

class Command(BaseCommand):
    help = 'Seed the database with example cards'

    def handle(self, *args, **kwargs):
        # Create or retrieve rarity
        rarity, _ = Rarity.objects.get_or_create(
            title="Legendary",
            defaults={
                'description': 'Very hard-to-get cards',
                'probability': 0.05
            }
        )

        # Create or retrieve card set
        initial_set, _ = CardSet.objects.get_or_create(
            title="Unleashed Arcana",
            defaults={
                'description': 'First collection of cards',
                'image': 'https://example.com/initial-set.jpg'
            }
        )

        # List of cards to add
        cards = [
            {
                "title": "Latra",
                "description": "Returns your fourth-year cards to the first year.",
                "image": "https://inkscape.app/wp-content/uploads/imagen-vectorial.webp",
            },
            {
                "title": "Torres",
                "description": "Forces you to rewrite your thesis every week.",
                "image": "https://example.com/torres.jpg",
            },
            {
                "title": "Martínez",
                "description": "When it enters the field, all students fall asleep.",
                "image": "https://example.com/martinez.jpg",
            },
            {
                "title": "Lab Beast",
                "description": "A legendary creature hungry for projects.",
                "image": "https://example.com/bestia.jpg",
            }
        ]

        # Create cards
        for card_data in cards:
            card, created = Card.objects.get_or_create(
                title=card_data["title"],
                defaults={
                    "description": card_data["description"],
                    "image": card_data["image"],
                    "rarity": rarity,
                    "card_set": initial_set
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Card '{card.title}' created"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Card '{card.title}' already exists"))
