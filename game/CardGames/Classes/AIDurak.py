from CardGames.Classes.Card import Card
from CardGames.Classes.Player import Player

class AIDurak(Player):
    def __init__(self, name):
        Player.__init__(self, name)
        self.seen_cards = set()
        self.player_hand_estimate = set()

        self._full_deck = {Card(rank, suit) for suit in Card.suits for rank in Card.ranks}
        self._unseen_cache = None
        self._cache_dirty = True

    def _update_unseen_cache(self):
        if self._cache_dirty:
            known = self.seen_cards | set(self.hand)
            self._unseen_cache = list(self._full_deck - known)
            self._cache_dirty = False

    def _mark_dirty(self):
        self._cache_dirty = True

    def remember_card(self, card):
        if card not in self.seen_cards:
            self.seen_cards.add(card)
            self._mark_dirty()

    def remember_table(self, table):
        for attack_card, (beaten, defend_card) in table.table.items():
            self.remember_card(attack_card)
            if defend_card:
                self.remember_card(defend_card)

    def remember_discard(self, discard_iterable):
        for c in discard_iterable:
            self.remember_card(c)

    def draw_from_deck(self, deck, trump_suit=None, good_prob=0.0):
        before = len(self.hand)
        if good_prob and good_prob != 0.0:
            self.hand.extend(deck.deal_biased(len(self.hand), good_prob))
        else:
            self.hand.extend(deck.deal(len(self.hand)))
        for c in self.hand[before:]:
            self.remember_card(c)
        self.sort_hand(trump_suit)

    def unseen_cards(self):
        self._update_unseen_cache()
        return self._unseen_cache

    def known_remaining_cards(self):
        self._update_unseen_cache()
        return self._unseen_cache

    def estimate_player_has_trumps(self, trump_suit):
        self._update_unseen_cache()
        return any(c.suit == trump_suit for c in self._unseen_cache)

    def choose_throw_ins(self, table, defender_hand_size, trump_suit):
        if defender_hand_size <= 0:
            return []

        table_ranks = table.ranks
        candidates = [c for c in self.hand if c.rank in table_ranks]
        candidates.sort(key=lambda c: (c.suit == trump_suit, Card.rank_values[c.rank]))

        return candidates[:defender_hand_size]

    def choose_attack_cards(self, table, trump_suit, defender_hand_size):
        if defender_hand_size <= 0:
            return []

        has_trump_left = self.estimate_player_has_trumps(trump_suit)
        table_ranks = table.ranks
        hand_sorted = sorted(self.hand, key=lambda c: (c.suit == trump_suit, Card.rank_values[c.rank]))

        attack_cards = []

        if not table:
            first = next((c for c in hand_sorted if c.suit != trump_suit), hand_sorted[0])
            attack_cards.append(first)
            for c in hand_sorted:
                if len(attack_cards) >= defender_hand_size:
                    break
                if c is not first and c.rank == first.rank:
                    attack_cards.append(c)
        else:
            for c in hand_sorted:
                if len(attack_cards) >= defender_hand_size:
                    break
                if c.rank in table_ranks:
                    if has_trump_left and c.suit != trump_suit:
                        attack_cards.append(c)
                    elif not has_trump_left:
                        attack_cards.append(c)
                    else:
                        attack_cards.append(c)

        return attack_cards

    def defense(self, attack_card, trump_suit):
        has_trump_left = self.estimate_player_has_trumps(trump_suit)
        candidates = [c for c in self.hand if Card.beats(c, attack_card, trump_suit)]
        if not candidates:
            return None

        candidates.sort(key=lambda c: (c.suit == trump_suit, Card.rank_values[c.rank]))
        if has_trump_left:
            for c in candidates:
                if c.suit != trump_suit:
                    return c
        return candidates[0]
