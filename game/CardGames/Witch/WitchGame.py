# -*- coding: utf-8 -*-
import random
from game.CardGames.Classes.Deck import Deck
from game.CardGames.Classes.Player import Player
from game.CardGames.Classes.AIWitch import AIWitch


class WitchGame:
    """
    'Ведьма' (K♠ = Witch) — Human vs AI, 36-card deck (6..A).
    Minimal state machine with separate user/ai turns; no console I/O, no checks.
    States: idle -> player_turn/opponent_turn <-> wait_choice -> game_over

    NOTE: No automatic pair-dropping anywhere. Use drop_pairs(...) explicitly.
    """

    def __init__(self, player_name="Вы", opponent_name="Противник", biased_draw=None):
        self.deck = Deck()
        self.player = Player(player_name)
        self.opponent = AIWitch(opponent_name)
        self.players = [self.player, self.opponent]

        # biased draw setup
        self.bias = {"player": 0.0, "opponent": 0.0}
        if biased_draw:
            who, prob = biased_draw
            prob = float(prob)
            if who == "player":
                self.bias["player"] = prob
            elif who == "opponent":
                self.bias["opponent"] = prob

        self.first_player = None
        self.current_idx = 0

        self.state = "idle"
        self.result = None
        self.pending_choice = None        # {"type": "exchange"/"drain", "taker": idx, "donor": idx}
        self._resume_state = None         # "player_turn" or "opponent_turn" to continue after wait_choice

    # ---------- bias helper ----------
    def _bias_idx(self, idx):
        return self.bias["player"] if idx == 0 else self.bias["opponent"]

    # ---------- public api ----------
    def start_round(self):
        self.deck = Deck()
        for p in self.players:
            p.hand = []
        # initial deal (NO auto-drop/shuffle)
        for i, p in enumerate(self.players):
            p.draw_from_deck(self.deck, trump_suit=None, good_prob=self._bias_idx(i))

        if self.first_player is None:
            self.first_player = random.choice([0, 1])
        self.current_idx = self.first_player

        self.result = None
        self.pending_choice = None
        self._resume_state = None
        self.state = "player_turn" if self.current_idx == 0 else "opponent_turn"

    def need_choice(self):
        if self.state == "wait_choice":
            donor = self.players[self.pending_choice["donor"]]
            return {
                "type": self.pending_choice["type"],
                "taker": self.pending_choice["taker"],
                "donor": self.pending_choice["donor"],
                "num_options": len(donor.hand),
            }
        return None

    def choose(self, index):
        donor = self.players[self.pending_choice["donor"]]
        taker = self.players[self.pending_choice["taker"]]
        taken = taker.take_card_from(donor, index=index)
        if hasattr(taker, 'on_after_take'):
            taker.on_after_take(donor, taken)
        # NO auto-drop/shuffle here
        self.pending_choice = None
        self.state = self._resume_state
        self._resume_state = None

    # ---------- helpers ----------
    def draw_up_to_six(self, idx):
        p = self.players[idx]
        while len(p.hand) < 6 and not self.deck.is_empty():
            p.draw_from_deck(self.deck, trump_suit=None, good_prob=self._bias_idx(idx))

    def _next_player_with_cards(self, start_idx):
        n = len(self.players)
        j = (start_idx + 1) % n
        while j != start_idx and len(self.players[j].hand) == 0:
            j = (j + 1) % n
        return j

    def game_over(self):
        a, b = self.players
        if len(a.hand) == 1 and len(b.hand) == 1:
            if a.has_only_witch():
                return True, a
            if b.has_only_witch():
                return True, b
        return False, None

    def _should_drain(self):
        a, b = self.players
        if len(a.hand) == 0 and len(b.hand) >= 2:
            return 0, 1
        if len(b.hand) == 0 and len(a.hand) >= 2:
            return 1, 0
        return None, None
