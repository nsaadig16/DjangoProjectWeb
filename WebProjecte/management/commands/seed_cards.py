from django.core.management.base import BaseCommand
from WebProjecte.models import Card, Rarity, CardSet

class Command(BaseCommand):
    help = 'Seed the database with example cards'

    def handle(self, *args, **kwargs):
        # Create or retrieve rarities
        legendary_rarity, _ = Rarity.objects.get_or_create(
            title="Legendary",
            defaults={
                'description': 'Very hard-to-get cards',
                'probability': 0.05
            }
        )
        epic_rarity, _ = Rarity.objects.get_or_create(
            title="Epic",
            defaults={
                'description': 'Hard-to-get cards',
                'probability': 0.15
            }
        )

        # Create or retrieve card set
        initial_set, _ = CardSet.objects.get_or_create(
            title="Unleashed Arcana",
            defaults={
                'description': 'First collection of cards',
                'image': 'card_sets/Envelope_UNLEASHED_ARCANE.png'
            }
        )

        # List of cards to add
        cards = [
            {
                "title": "Teacher Latra",
                "description": "Returns your fourth-year cards to the first year.",
                "image": "card_images/unleashed_arcane/PROFESSOR_LATRA.png",
                "rarity": legendary_rarity,
            },
            {
                "title": "Teacher David",
                "description": "A wise professor who guides students through complex topics.",
                "image": "card_images/unleashed_arcane/PROFESSOR_DAVID.png",
                "rarity": legendary_rarity,
            },
            {
                "title": "Teacher Miret",
                "description": "An enthusiastic teacher who makes learning an adventure.",
                "image": "card_images/unleashed_arcane/PROFESSOR_MIRET.png",
                "rarity": legendary_rarity,
            },
            {
                "title": "Teacher Planes",
                "description": "A meticulous instructor focused on the fundamentals.",
                "image": "card_images/unleashed_arcane/PROFESSOR_PLANES.png",
                "rarity": legendary_rarity,
            },
            {
                "title": "Teacher Roberto",
                "description": "A supportive mentor who encourages independent thinking.",
                "image": "card_images/unleashed_arcane/PROFESSOR_ROBERTO.png",
                "rarity": legendary_rarity,
            },
            {
                "title": "Student David",
                "description": "A diligent student always eager to learn.",
                "image": "card_images/unleashed_arcane/STUDENT_DAVID.png",
                "rarity": epic_rarity,
            },
            {
                "title": "Student Latra",
                "description": "A resourceful student who finds creative solutions.",
                "image": "card_images/unleashed_arcane/STUDENT_LATRA.png",
                "rarity": epic_rarity,
            },
            {
                "title": "Student Miret",
                "description": "An inquisitive student with a passion for discovery.",
                "image": "card_images/unleashed_arcane/STUDENT_MIRET.png",
                "rarity": epic_rarity,
            },
            {
                "title": "Student Planes",
                "description": "A focused student with a knack for organization.",
                "image": "card_images/unleashed_arcane/STUDENT_PLANES.png",
                "rarity": epic_rarity,
            },
            {
                "title": "Student Roberto",
                "description": "A collaborative student who enjoys teamwork.",
                "image": "card_images/unleashed_arcane/STUDENT_ROBERTO.png",
                "rarity": epic_rarity,
            }
        ]

        # Create cards
        for card_data in cards:
            card, created = Card.objects.get_or_create(
                title=card_data["title"],
                defaults={
                    "description": card_data["description"],
                    "image": card_data["image"],
                    "rarity": card_data["rarity"],
                    "card_set": initial_set
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Card '{card.title}' created"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Card '{card.title}' already exists"))