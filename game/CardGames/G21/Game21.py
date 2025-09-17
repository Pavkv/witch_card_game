# coding=utf-8
import random

from CardGames.Classes.Card import Card
from CardGames.Classes.Player import Player
from CardGames.Classes.Deck import Deck
from CardGames.Classes.AI21 import AI21


class Game21:
    def __init__(self, player_name="Вы", opponent_name="Противник", biased_draw=None, initial_deal=2, aces_low=False):
        self.deck = Deck()
        self.player = Player(player_name, aces_low)
        self.opponent = AI21(opponent_name, aces_low)
        self.first_player = None
        self.state = "idle"
        self.result = None

        self.initial_deal = initial_deal
        self.aces_low = aces_low

        self.bias = {"player": 0.0, "opponent": 0.0}
        if biased_draw:
            who, prob = biased_draw
            prob = float(prob)
            if who == "player":
                self.bias["player"] = prob
            elif who == "opponent":
                self.bias["opponent"] = prob

        self.that_s_him = False  # special flag for "That’s him!" achievement
        self.all_in_place = False  # special flag for "All in place" achievement

    # ---------- internals ----------
    def _clear_hands(self):
        self.player.hand = []
        self.opponent.hand = []

    def _maybe_refresh_deck(self):
        if len(self.deck.cards) < 10:
            self.deck = Deck()

    def _draw_one(self, who):
        prob = self.bias["player"] if who is self.player else self.bias["opponent"]
        c = self.deck.draw_with_bias(prob) if prob > 0.0 else self.deck.draw_top()
        if c is not None:
            if who is self.player and Card('A', 'S') in who.hand and c == Card('A', 'D'):
                self.all_in_place = True
            if who is self.player and c.rank == 'A' and who.total21() + 11 == 22:
                self.that_s_him = True
            who.hand.append(c)
        return c

    def _deal_n_each(self):
        for _ in range(self.initial_deal):
            self._draw_one(self.player)
            self._draw_one(self.opponent)

    def _instant_check(self):
        if self.player.total21() == 21:
            self.finalize(winner=self.player)
            return True
        if self.opponent.total21() == 21:
            self.finalize(winner=self.opponent)
            return True
        return False

    def start_round(self):
        self._maybe_refresh_deck()
        self._clear_hands()
        self.result = None
        self.state = "initial_deal"
        self._deal_n_each()
        if self._instant_check():
            return

        if self.first_player is None:
            self.first_player = random.choice([self.player, self.opponent])

        self.state = "player_turn" if self.first_player == self.player else "opponent_turn"

    def opponent_turn(self):
        return self.opponent.decide(seen_cards=list(self.opponent.hand), opponent_total=self.player.total21())

    def finalize(self, winner=None):
        if winner is self.player:
            self.result = self.player.name
        elif winner is self.opponent:
            self.result = self.opponent.name
        else:
            ht, at = self.player.total21(), self.opponent.total21()
            hb, ab = self.player.is_bust21(), self.opponent.is_bust21()
            if hb and ab:
                self.result = "draw"
            elif hb:
                self.result = self.opponent.name
            elif ab:
                self.result = self.player.name
            elif ht == at:
                self.result = "draw"
            elif ht > at:
                self.result = self.player.name
            else:
                self.result = self.opponent.name
