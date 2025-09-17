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

    # ---------- user / ai turn flows ----------
    def player_turn(self):
        over, loser = self._game_over()
        if over:
            self.result = loser.name
            return

        cur = self.players[0]
        # draw-to-six WITHOUT cleanup
        self._draw_up_to_six(idx=0)

        # exchange (human chooses)
        if cur.can_exchange_now(self.deck):
            donor_idx = self._next_player_with_cards(0)
            self.pending_choice = {"type": "exchange", "taker": 0, "donor": donor_idx}
            self._resume_state = "player_turn"
            self.state = "wait_choice"
            return

        # endgame drain loop (no auto-drop after transfers)
        while True:
            over, loser = self._game_over()
            if over:
                self.result = loser.name
                return

            taker_idx, donor_idx = self._should_drain()
            if taker_idx is None:
                break

            if taker_idx == 0:
                self.pending_choice = {"type": "drain", "taker": 0, "donor": donor_idx}
                self._resume_state = "player_turn"
                self.state = "wait_choice"
                return
            else:
                taker = self.players[1]
                donor = self.players[0]
                ai_idx = taker.choose_drain_index(donor) if hasattr(taker, "choose_drain_index") else random.randrange(len(donor.hand))
                taken = taker.take_card_from(donor, index=ai_idx)
                if hasattr(taker, 'on_after_take'):
                    taker.on_after_take(donor, taken)
                # NO auto-drop/shuffle here

        # switch to AI turn
        self.current_idx = self._next_player_with_cards(0)
        self.state = "opponent_turn"

    def opponent_turn(self):
        over, loser = self._game_over()
        if over:
            self.result = loser.name
            return

        cur = self.players[1]
        # draw-to-six WITHOUT cleanup
        self._draw_up_to_six(idx=1)

        # exchange (AI auto)
        if cur.can_exchange_now(self.deck):
            donor_idx = self._next_player_with_cards(1)
            donor = self.players[donor_idx]
            ai_idx = cur.choose_exchange_index(donor) if hasattr(cur, "choose_exchange_index") else random.randrange(len(donor.hand))
            taken = cur.take_card_from(donor, index=ai_idx)
            if hasattr(cur, 'on_after_take'):
                cur.on_after_take(donor, taken)
            # NO auto-drop/shuffle here

        # endgame drain loop (no auto-drop after transfers)
        while True:
            over, loser = self._game_over()
            if over:
                self.result = loser.name
                return

            taker_idx, donor_idx = self._should_drain()
            if taker_idx is None:
                break

            if taker_idx == 0:
                self.pending_choice = {"type": "drain", "taker": 0, "donor": donor_idx}
                self._resume_state = "opponent_turn"
                self.state = "wait_choice"
                return
            else:
                taker = self.players[1]
                donor = self.players[0]
                ai_idx = taker.choose_drain_index(donor) if hasattr(taker, "choose_drain_index") else random.randrange(len(donor.hand))
                taken = taker.take_card_from(donor, index=ai_idx)
                if hasattr(taker, 'on_after_take'):
                    taker.on_after_take(donor, taken)
                # NO auto-drop/shuffle here

        # switch to user turn
        self.current_idx = self._next_player_with_cards(1)
        self.state = "player_turn"

    # ---------- helpers ----------
    def _draw_up_to_six(self, idx):
        p = self.players[idx]
        while len(p.hand) < 6 and not self.deck.is_empty():
            p.draw_from_deck(self.deck, trump_suit=None, good_prob=self._bias_idx(idx))

    def _next_player_with_cards(self, start_idx):
        n = len(self.players)
        j = (start_idx + 1) % n
        while j != start_idx and len(self.players[j].hand) == 0:
            j = (j + 1) % n
        return j

    def _game_over(self):
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
