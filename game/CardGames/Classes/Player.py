# coding=utf-8
import random
from Card import Card


class Player(object):
    def __init__(self, name, aces_low=False):
        self.name = name
        self.hand = []
        self.aces_low = aces_low

    def __str__(self):
        return "Player {} has {} cards: {}".format(
            self.name, len(self.hand), ", ".join(str(c) for c in self.hand)
        )

    def __len__(self):
        return len(self.hand)

    def draw_from_deck(self, deck, trump_suit=None, good_prob=0.0):
        if good_prob != 0.0:
            self.hand.extend(deck.deal_biased(len(self.hand), good_prob))
        else:
            self.hand.extend(deck.deal(len(self.hand)))
        if trump_suit is not None:
            self.sort_hand(trump_suit)

    def sort_hand(self, trump_suit):
        def card_sort_key(card):
            is_trump = (card.suit == trump_suit)
            rank_value = Card.rank_values[card.rank]
            return is_trump, rank_value

        self.hand.sort(key=card_sort_key)

    def lowest_trump_card(self, trump):
        trump_cards = [card for card in self.hand if card.suit == trump]
        if not trump_cards:
            return None
        return min(trump_cards, key=lambda card: Card.rank_values[card.rank])

    def total21(self):
        total = 0
        aces = 0
        for c in self.hand:
            pts = Card.points21_map[c.rank]
            if c.rank == 'A':
                aces += 1
            total += pts

        if self.aces_low:
            while total > 21 and aces > 0:
                total -= 10
                aces -= 1

        return total

    def is_bust21(self):
        return self.total21() > 21

    def is_natural21(self):
        return len(self.hand) == 2 and self.total21() == 21

    def get_ranks(self):
        return [card.rank for card in self.hand]

    def shaffle_hand(self):
        random.shuffle(self.hand)

    def has_only_witch(self):
        """True if player holds exactly one card and it is the Witch."""
        return len(self.hand) == 1 and Card.is_witch_card(self.hand[0])

    def _pair_buckets_excluding_witch(self):
        """
        Internal: group cards by rank, excluding the Witch.
        Returns (rank_to_cards, witches_list)
        """
        buckets = {}
        witches = []
        for c in self.hand:
            if Card.is_witch_card(c):
                witches.append(c)
            else:
                buckets.setdefault(c.rank, []).append(c)
        return buckets, witches

    def count_pairs_excluding_witch(self):
        """How many pairs are currently in hand, ignoring K♠."""
        buckets, _ = self._pair_buckets_excluding_witch()
        return sum(len(cards) // 2 for cards in buckets.itervalues())

    def discard_pairs_excluding_witch(self, deck):
        """
        Discard ALL possible pairs by rank, but NEVER use/discard the Witch (K♠).
        Keeps at most one leftover per rank. Returns number of cards discarded.
        """
        buckets, witches = self._pair_buckets_excluding_witch()

        # Keep one leftover card for odd counts
        keep_cards = []
        for rank, cards in buckets.iteritems():
            if len(cards) % 2 == 1:
                keep_cards.append(cards[0])

        # Always keep all witches (cannot be discarded)
        keep_cards.extend(witches)

        before = len(self.hand)
        # Rebuild hand with kept cards only (stable: keep original order where possible)
        # Use a multiset of objects to preserve identity
        keep_multiset = {}
        for c in keep_cards:
            keep_multiset[c] = keep_multiset.get(c, 0) + 1

        new_hand = []
        for c in self.hand:
            if keep_multiset.get(c, 0) > 0:
                new_hand.append(c)
                keep_multiset[c] -= 1
            else:
                deck.discard.append(c)
        self.hand = new_hand

        return before - len(self.hand)

    def can_exchange_now(self, deck):
        """
        Exchange phase starts if:
        - deck is empty, OR
        - hand already has 6 and there are no pairs to discard.
        """
        return deck.is_empty() or (len(self.hand) >= 6 and self.count_pairs_excluding_witch() == 0)

    def take_card_from(self, other_player, index=None, rng=None):
        """
        Take ONE card from another player's hand.
        - If index is None: pick a random index.
        - Returns the card taken (or None if other has no cards).
        """
        if not other_player.hand:
            return None
        if index is None:
            import random as _r
            r = rng or _r
            index = r.randrange(len(other_player.hand))
        card = other_player.hand.pop(index)
        self.hand.append(card)
        return card