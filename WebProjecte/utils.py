import random
from .models import Card, CollectionCard, Rarity , Collection

def get_random_card():
    rarities = Rarity.objects.all()
    weighted_choices = []

    for rarity in rarities:
        cards = Card.objects.filter(rarity=rarity)
        for card in cards:
            weighted_choices.append((card, rarity.probability))

    selected = random.choices(
        [card for card, prob in weighted_choices],
        weights=[prob for card, prob in weighted_choices],
        k=1
    )[0]
    return selected

def open_pack(user, num_cards=5):
    collection, _ = Collection.objects.get_or_create(user=user)
    obtained_cards = []

    for _ in range(num_cards):
        card = get_random_card()
        cc, created = CollectionCard.objects.get_or_create(
            collection=collection,
            card=card,
            defaults={'quantity': 1}
        )
        if not created:
            cc.quantity += 1
            cc.save()
        obtained_cards.append(card)

    return obtained_cards
