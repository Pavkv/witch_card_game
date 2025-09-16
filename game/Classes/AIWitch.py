# -*- coding: utf-8 -*-
from __future__ import print_function
import random
from Card import Card
from Player import Player

class AIWitch(Player):
    """
    Advanced AI for the Witch game (KS = Witch).
    Inherits from Player, so it can be used as a direct replacement for a Player
    instance in WitchGame (hand, draw, discard, take, etc. all work the same).

    Strategy: epsilon-greedy bandit that learns which donor indices (0..N-1)
    are better for yielding immediate pairs while avoiding KS.
    - Rewards an index if taken card's rank matched a rank already in AI's hand
      BEFORE the take (so a pair can be discarded right away).
    - Penalizes an index if the taken card is KS.
    - Soft decay to favor recent evidence.
    """

    def __init__(self, name='ИИ', aces_low=False,
                 rng=None, epsilon=0.20, reward=1.0, witch_penalty=1.5,
                 decay=0.995, min_trials_boost=0.25, verbose=False):
        super(AIWitch, self).__init__(name, aces_low)
        self.rng = rng or random
        self.epsilon = float(epsilon)
        self.reward = float(reward)
        self.witch_penalty = float(witch_penalty)
        self.decay = float(decay)
        self.min_trials_boost = float(min_trials_boost)
        self.verbose = bool(verbose)

        # stats[donor_size] = list of {"score": float, "trials": int} per index
        self.stats = {}

        # Pending context for learning after a take
        self._pending_context = None  # {"donor_size": int, "index": int, "taker_ranks": set}

    # ------------------------- Decision API -------------------------

    def choose_exchange_index(self, donor_player):
        """
        Choose which index to take from donor during NORMAL EXCHANGE on our turn.
        Records our ranks BEFORE the take for learning.
        """
        idx = self._choose_index(donor_player)
        if idx is None:
            return None
        self._remember_context(donor_player, idx)
        return idx

    def choose_drain_index(self, donor_player):
        """
        Choose which index to take during ENDGAME DRAIN (when opponent has >=2 and we have 0).
        Same policy as exchange by default.
        """
        idx = self._choose_index(donor_player)
        if idx is None:
            return None
        self._remember_context(donor_player, idx)
        return idx

    def on_after_take(self, donor_player, taken_card):
        """
        Call this immediately after self.take_card_from(donor, index=idx).
        Uses the pending context to update stats:
         - +reward if taken_card.rank was already in our hand before the take (pair possible)
         - -witch_penalty if the card is the Witch (KS)
        """
        ctx = self._pending_context
        self._pending_context = None
        if ctx is None:
            return

        donor_size = ctx["donor_size"]
        index = ctx["index"]
        my_ranks_before = ctx["taker_ranks"]

        # Ensure stats capacity
        self._ensure_stats_capacity(donor_size)

        # Decay all entries a bit for this donor size
        self._decay_stats(donor_size)

        # Outcome
        score_delta = 0.0

        # Witch penalty
        if Card.is_witch_card(taken_card):
            score_delta -= self.witch_penalty

        # Pair-ability reward (skip rewarding if it was the Witch)
        elif getattr(taken_card, "rank", None) in my_ranks_before:
            score_delta += self.reward

        # Apply update
        self.stats[donor_size][index]["score"] += score_delta
        self.stats[donor_size][index]["trials"] += 1

        if self.verbose:
            print("[AI {}] donor_size={} idx={} delta={:+.2f} -> score={:.2f} trials={}".format(
                self.name, donor_size, index, score_delta,
                self.stats[donor_size][index]["score"],
                self.stats[donor_size][index]["trials"]
            ))

    # Optional hook if you ever want to react after discards
    def on_after_discard(self):
        return

    # ------------------------- Internals -------------------------

    def _choose_index(self, donor_player):
        n = len(donor_player.hand)
        if n <= 0:
            return None
        self._ensure_stats_capacity(n)

        # epsilon-greedy
        if self.rng.random() < self.epsilon:
            return self.rng.randrange(n)

        # pick argmax(score + prior/(1+trials))
        best_idx, best_val = None, None
        for i in range(n):
            s = self.stats[n][i]
            val = s["score"] + self.min_trials_boost / (1.0 + s["trials"])
            if best_val is None or val > best_val:
                best_val = val
                best_idx = i
        return best_idx if best_idx is not None else self.rng.randrange(n)

    def _remember_context(self, donor_player, index):
        # Ranks BEFORE the take (to judge pair potential fairly)
        my_ranks_before = set(c.rank for c in self.hand)
        self._pending_context = {
            "donor_size": len(donor_player.hand),
            "index": index,
            "taker_ranks": my_ranks_before
        }

    def _ensure_stats_capacity(self, donor_size):
        if donor_size not in self.stats:
            self.stats[donor_size] = [{"score": 0.0, "trials": 0} for _ in range(donor_size)]
        else:
            # resize if donor size changed
            cur = len(self.stats[donor_size])
            if donor_size > cur:
                self.stats[donor_size].extend({"score": 0.0, "trials": 0} for _ in range(donor_size - cur))
            elif donor_size < cur:
                self.stats[donor_size] = self.stats[donor_size][:donor_size]

    def _decay_stats(self, donor_size):
        if donor_size in self.stats:
            for entry in self.stats[donor_size]:
                entry["score"] *= self.decay
