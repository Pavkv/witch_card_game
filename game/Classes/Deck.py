import random
from Card import Card

class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Card.suits for rank in Card.ranks]
        self.discard = []
        self.shuffle()
        self.trump_card = self.get_trump_card()
        self.trump_suit = self.trump_card.suit if self.trump_card else None

    def shuffle(self):
        random.shuffle(self.cards)

    def get_trump_card(self):
        return self.cards[-1] if self.cards else None

    def draw_top(self):
        return self.cards.pop(0) if self.cards else None

    def deal(self, current_hand_size):
        need = max(0, 6 - current_hand_size)
        take = min(need, len(self.cards))
        return [self.draw_top() for _ in range(take)]

    def draw_with_bias(self, good_prob):
        if not self.cards:
            return None

        search_slice = self.cards[:-1] if len(self.cards) > 1 else []

        if search_slice and random.random() < float(good_prob):
            good_idxs = [i for i, c in enumerate(search_slice) if c.is_good_card(self.trump_suit)]
            if good_idxs:
                return self.cards.pop(random.choice(good_idxs))

        return self.draw_top()

    def deal_biased(self, current_hand_size, good_prob):
        need = max(0, 6 - current_hand_size)
        take = min(need, len(self.cards))
        return [self.draw_with_bias(good_prob) for _ in range(take)]

    def is_empty(self):
        return len(self.cards) == 0

    def remaining(self):
        return len(self.cards)