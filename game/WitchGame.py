# -*- coding: utf-8 -*-
import random
from Classes.Deck import Deck
from Classes.Player import Player
from Classes.AIWitch import AIWitch

class WitchGame(object):
    """
    'Ведьма' (K♠ = Witch) — Human vs AI, 36-card deck (6..A).
    Refactored to a state machine (no console I/O).
    Drive it from UI with: step() / need_choice() / choose(idx).
    """

    # --- State constants (strings to keep Py2 compatibility without Enum) ---
    S_INIT             = "INIT"
    S_DEAL             = "DEAL"
    S_TURN_START       = "TURN_START"
    S_DRAW_DISCARD     = "DRAW_DISCARD"
    S_EXCHANGE_CHECK   = "EXCHANGE_CHECK"
    S_EXCHANGE_WAIT    = "EXCHANGE_WAIT"   # waiting for human to choose a card during exchange
    S_ENDGAME_DRAIN    = "ENDGAME_DRAIN"
    S_DRAIN_WAIT       = "DRAIN_WAIT"      # waiting for human to choose a card during endgame drain
    S_POST_BALANCE     = "POST_BALANCE"
    S_TURN_SWITCH      = "TURN_SWITCH"
    S_GAME_OVER        = "GAME_OVER"

    # pending_choice["type"] is one of: "exchange" or "drain"

    def __init__(self, good_prob_human=0.0, good_prob_ai=0.0, seed=None):
        if seed is not None:
            random.seed(seed)

        self.deck = Deck()
        # Players
        self.player   = Player(name='Вы', aces_low=False)
        self.opponent = AIWitch(
            name='ИИ', aces_low=False, rng=random, epsilon=0.20,
            reward=1.0, witch_penalty=1.5, decay=0.995, min_trials_boost=0.25
        )
        self.players = [self.player, self.opponent]

        # Per-player “good card” draw probabilities
        self.good_prob = {0: float(good_prob_human), 1: float(good_prob_ai)}

        # Turn & state
        self.current_idx = 0
        self.state = self.S_INIT

        # Choice that the human must make (None if not waiting)
        self.pending_choice = None  # dict: {"type": "exchange"|"drain", "taker": idx, "donor": idx}

        # Outcome
        self.game_over = False
        self.loser = None

        # Optional: event log for UI (strings or small dicts)
        self.events = []

    # ---------- Public UI helpers ----------
    def need_choice(self):
        """Return a dict describing the needed choice or None.
        Example:
        {
          "type": "exchange"|"drain",
          "taker": 0,
          "donor": 1,
          "num_options": 5,            # how many face-down cards to pick from (indices 0..n-1)
          "opponent_len": 5            # same as num_options, explicit for UI convenience
        }
        """
        if self.pending_choice is None:
            return None
        donor = self.players[self.pending_choice["donor"]]
        return {
            "type": self.pending_choice["type"],
            "taker": self.pending_choice["taker"],
            "donor": self.pending_choice["donor"],
            "num_options": len(donor.hand),
            "opponent_len": len(donor.hand),
        }

    def choose(self, index):
        """Feed the human's chosen index for the current pending choice and advance."""
        if self.pending_choice is None:
            raise RuntimeError("No choice is pending right now.")

        donor = self.players[self.pending_choice["donor"]]
        if not (0 <= index < len(donor.hand)):
            raise ValueError("Invalid index {} (0..{}).".format(index, max(0, len(donor.hand)-1)))

        ctype = self.pending_choice["type"]
        taker = self.players[self.pending_choice["taker"]]

        # Perform the action
        taken = taker.take_card_from(donor, index=index)
        self.events.append({"evt": "take", "type": ctype, "taker": taker.name, "donor": donor.name, "card": str(taken)})

        # AI hooks
        if hasattr(taker, 'on_after_take'):
            taker.on_after_take(donor, taken)

        # After each transfer, discard pairs and shuffle
        taker.discard_pairs_excluding_witch()
        donor.discard_pairs_excluding_witch()
        taker.shaffle_hand()
        donor.shaffle_hand()

        # Clear choice and continue the state machine
        if ctype == "exchange":
            self.pending_choice = None
            self.state = self.S_ENDGAME_DRAIN  # continue normal flow
        elif ctype == "drain":
            self.pending_choice = None
            self.state = self.S_ENDGAME_DRAIN  # keep draining loop until done
        else:
            raise RuntimeError("Unknown pending choice type: {}".format(ctype))

        # Auto-advance after applying the choice
        self.step()

    # ---------- Core state machine driver ----------
    def step(self):
        """
        Advance the game until:
          - a human choice is needed (need_choice() becomes non-None), or
          - the game reaches GAME_OVER.
        Safe to call repeatedly after UI actions.
        """
        while True:
            # If we're waiting for a choice, stop here.
            if self.pending_choice is not None:
                return

            # If game ended, stop.
            if self.state == self.S_GAME_OVER:
                return

            # Dispatch by state:
            if self.state == self.S_INIT:
                self._on_init()
            elif self.state == self.S_DEAL:
                self._on_deal()
            elif self.state == self.S_TURN_START:
                self._on_turn_start()
            elif self.state == self.S_DRAW_DISCARD:
                self._on_draw_discard()
            elif self.state == self.S_EXCHANGE_CHECK:
                self._on_exchange_check()
            elif self.state == self.S_ENDGAME_DRAIN:
                # This may set a DRAIN_WAIT (human choice) or fall through to POST_BALANCE
                self._on_endgame_drain()
            elif self.state == self.S_POST_BALANCE:
                self._on_post_balance()
            elif self.state == self.S_TURN_SWITCH:
                self._on_turn_switch()
            elif self.state == self.S_EXCHANGE_WAIT or self.state == self.S_DRAIN_WAIT:
                # Human must call choose(index). Pause here.
                return
            else:
                raise RuntimeError("Unknown state: {}".format(self.state))

    # ---------- State handlers ----------
    def _on_init(self):
        # Validate deck size (no printing, but optional event)
        if len(self.deck.cards) not in (36, 35):
            self.events.append({"evt": "warn", "msg": "Deck is not standard 36 cards (got {})".format(len(self.deck.cards))})
        self.state = self.S_DEAL

    def _on_deal(self):
        for i, p in enumerate(self.players):
            p.draw_from_deck(self.deck, trump_suit=None, good_prob=self.good_prob[i])
            p.discard_pairs_excluding_witch()
            p.shaffle_hand()
        self.state = self.S_TURN_START

    def _on_turn_start(self):
        over, loser = self._game_over()
        if over:
            self._finish_game(loser)
            return
        # Proceed with the current player's normal phases
        self.state = self.S_DRAW_DISCARD

    def _on_draw_discard(self):
        self._draw_discard_phase(self.current_idx)
        self.state = self.S_EXCHANGE_CHECK

    def _on_exchange_check(self):
        cur = self.players[self.current_idx]
        if cur.can_exchange_now(self.deck):
            if self.current_idx == 0:
                # Human must choose a card from AI
                donor_idx = self._next_player_with_cards(self.current_idx)
                self._set_pending_choice("exchange", self.current_idx, donor_idx)
                self.state = self.S_EXCHANGE_WAIT
                return
            else:
                # AI takes from human automatically
                donor_idx = self._next_player_with_cards(self.current_idx)
                donor = self.players[donor_idx]
                if hasattr(cur, 'choose_exchange_index'):
                    ai_idx = cur.choose_exchange_index(donor)
                else:
                    ai_idx = random.randrange(len(donor.hand))
                taken = cur.take_card_from(donor, index=ai_idx, rng=random)
                if hasattr(cur, 'on_after_take'):
                    cur.on_after_take(donor, taken)
                self.events.append({"evt": "take", "type": "exchange", "taker": cur.name, "donor": donor.name, "card": str(taken)})
                # Discard/shuffle after exchange
                cur.discard_pairs_excluding_witch()
                donor.discard_pairs_excluding_witch()
                cur.shaffle_hand()
                donor.shaffle_hand()
        # Continue to endgame drain regardless
        self.state = self.S_ENDGAME_DRAIN

    def _on_endgame_drain(self):
        # Drain may loop multiple times. Stop if human must choose.
        while True:
            over, loser = self._game_over()
            if over:
                self._finish_game(loser)
                return

            taker_idx, donor_idx = self._should_drain()
            if taker_idx is None:
                break

            taker = self.players[taker_idx]
            donor = self.players[donor_idx]
            if not donor.hand:
                break

            if taker_idx == 0:
                # Human must pick a card from donor (AI)
                self._set_pending_choice("drain", taker_idx, donor_idx)
                self.state = self.S_DRAIN_WAIT
                return
            else:
                # AI drains automatically
                if hasattr(taker, 'choose_drain_index'):
                    ai_idx = taker.choose_drain_index(donor)
                else:
                    ai_idx = random.randrange(len(donor.hand))
                taken = taker.take_card_from(donor, index=ai_idx, rng=random)
                if hasattr(taker, 'on_after_take'):
                    taker.on_after_take(donor, taken)
                self.events.append({"evt": "take", "type": "drain", "taker": taker.name, "donor": donor.name, "card": str(taken)})

                # After each transfer, discard pairs and shuffle
                taker.discard_pairs_excluding_witch()
                donor.discard_pairs_excluding_witch()
                taker.shaffle_hand()
                donor.shaffle_hand()

                # and loop to see if we must drain again

        # No more draining; proceed
        self.state = self.S_POST_BALANCE

    def _on_post_balance(self):
        self._post_turn_balance(self.current_idx)
        self.state = self.S_TURN_SWITCH

    def _on_turn_switch(self):
        self.current_idx = self._next_player_with_cards(self.current_idx)
        self.state = self.S_TURN_START

    # ---------- Internals reused from original (no printing) ----------
    def _next_player_with_cards(self, start_idx):
        n = len(self.players)
        j = (start_idx + 1) % n
        while j != start_idx and len(self.players[j].hand) == 0:
            j = (j + 1) % n
        return j

    def _game_over(self):
        a, b = self.players[0], self.players[1]
        if len(a.hand) == 1 and len(b.hand) == 1:
            a_witch = a.has_only_witch()
            b_witch = b.has_only_witch()
            if a_witch and not b_witch:
                return True, a
            if b_witch and not a_witch:
                return True, b
        return False, None

    def _draw_discard_phase(self, idx):
        p = self.players[idx]
        return p.draw_up_to_six_and_cleanup(self.deck, good_prob=self.good_prob[idx])

    def _should_drain(self):
        a, b = self.players[0], self.players[1]
        if len(a.hand) == 0 and len(b.hand) >= 2:
            return 0, 1  # A takes from B
        if len(b.hand) == 0 and len(a.hand) >= 2:
            return 1, 0  # B takes from A
        return None, None

    def _post_turn_balance(self, last_idx):
        if self.deck.is_empty():
            return
        donor = self.players[last_idx]
        if len(donor.hand) <= 6:
            return
        taker_idx = 1 - last_idx
        taker = self.players[taker_idx]
        while not self.deck.is_empty():
            if len(taker.hand) < 6:
                before = len(taker.hand)
                taker.draw_from_deck(self.deck, trump_suit=None, good_prob=self.good_prob[taker_idx])
                after = len(taker.hand)
                if after > before:
                    self.events.append({
                        "evt": "autodraw", "player": taker.name,
                        "delta": after - before, "now": after
                    })
            discarded = taker.discard_pairs_excluding_witch()
            if discarded:
                taker.shaffle_hand()
            if self.deck.is_empty():
                break
            if len(taker.hand) == 6 and taker.count_pairs_excluding_witch() == 0:
                break

    def _set_pending_choice(self, choice_type, taker_idx, donor_idx):
        self.pending_choice = {
            "type": choice_type,
            "taker": taker_idx,
            "donor": donor_idx
        }

    def _finish_game(self, loser):
        self.game_over = True
        self.loser = loser
        self.state = self.S_GAME_OVER
        self.events.append({"evt": "game_over", "loser": loser.name})
