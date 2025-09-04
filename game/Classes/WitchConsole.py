# -*- coding: utf-8 -*-
from __future__ import print_function
import random
from game.Classes.Deck import Deck
from game.Classes.Player import Player

class WitchGame(object):
    """
    'Ведьма' (K♠ = Witch) — Human vs AI, 36-card deck (6..A).
    Rules:
      - Deal 6 to each from the 36-card deck.
      - On your turn: auto-discard all pairs (excluding K♠).
      - If deck not empty and hand < 6, draw up to 6, then discard again.
      - If already 6 and no pairs OR deck is empty -> exchange:
        current player takes 1 card from next player.
      - K♠ cannot be discarded. Loser is whoever remains with K♠ at the end.
    """

    def __init__(self, good_prob_human=0.0, good_prob_ai=0.0, seed=None):
        if seed is not None:
            random.seed(seed)
        self.deck = Deck()
        # Sanity check: 36-card deck (not strictly required, but helpful)
        if len(self.deck.cards) not in (36, 35):  # 35 can happen if someone pre-drew before check
            print("Warning: expected a 36-card deck (6..A), got {}".format(len(self.deck.cards)))

        self.players = [
            Player(name='Вы', aces_low=False),  # Human
            Player(name='ИИ', aces_low=False)   # Simple AI
        ]
        self.good_prob = {0: float(good_prob_human), 1: float(good_prob_ai)}
        self.current_idx = 0
        self.trump_suit = self.deck.trump_suit  # only used for sorting visuals

    # ---------- Setup ----------
    def deal_initial(self):
        # Each player draws to 6, discards pairs (excluding Witch), sorts for display
        for i, p in enumerate(self.players):
            p.draw_from_deck(self.deck, trump_suit=self.trump_suit, good_prob=self.good_prob[i])
            p.discard_pairs_excluding_witch()
            p.sort_hand(self.trump_suit)

    # ---------- Utilities ----------
    def _next_player_with_cards(self, start_idx):
        n = len(self.players)
        j = (start_idx + 1) % n
        while j != start_idx and len(self.players[j].hand) == 0:
            j = (j + 1) % n
        return j

    def _game_over(self):
        active = [p for p in self.players if len(p.hand) > 0]
        if len(active) == 1 and active[0].has_only_witch():
            return True, active[0]  # loser
        return False, None

    def _hand_str(self, hand, reveal=True):
        if not hand:
            return '(пусто)'
        return ' '.join(str(c) if reveal else '▮' for c in (hand if reveal else hand))

    def _print_state(self, reveal_human=True):
        print("\n--- Состояние ---")
        print("Колода: {} карт".format(len(self.deck.cards)))
        print("{}: {}".format(self.players[0].name, self._hand_str(self.players[0].hand, reveal=reveal_human)))
        print("{}: {} [{}]".format(self.players[1].name, self._hand_str(self.players[1].hand, reveal=False), len(self.players[1].hand)))
        print("-----------------")

    # ---------- Turn Phases ----------
    def _draw_discard_phase(self, idx):
        p = self.players[idx]
        return p.draw_up_to_six_and_cleanup(self.deck, trump_suit=self.trump_suit, good_prob=self.good_prob[idx])

    def _exchange_phase(self, idx):
        cur = self.players[idx]
        nxt_i = self._next_player_with_cards(idx)
        if nxt_i == idx:
            return False
        nxt = self.players[nxt_i]
        if not nxt.hand:
            return False

        if idx == 0:
            print("\nОбмен: у {} карт {}".format(nxt.name, len(nxt.hand)))
            print("Их вид вы не знаете: {}".format(self._hand_str(nxt.hand, reveal=False)))
            while True:
                try:
                    choice = raw_input("Выберите индекс карты у {} (1..{}): ".format(nxt.name, len(nxt.hand)))
                    k = int(choice) - 1
                    if 0 <= k < len(nxt.hand):
                        break
                    print("Неверный индекс.")
                except Exception:
                    print("Введите число.")
            taken = cur.take_card_from(nxt, index=k)
            print("Вы взяли: [{}]".format(taken))
        else:
            cur.take_card_from(nxt, index=None, rng=random)
            print("\nИИ взял одну карту у {}.".format(nxt.name))

        cur.discard_pairs_excluding_witch()
        nxt.discard_pairs_excluding_witch()
        cur.sort_hand(self.trump_suit)
        nxt.sort_hand(self.trump_suit)
        return True

    # ---------- Game Loop ----------
    def run(self):
        print(u"Добро пожаловать в «Ведьма» (36 карт: 6..A). Не оставайтесь с KS в конце!")
        self.deal_initial()
        self._print_state(reveal_human=True)

        while True:
            over, loser = self._game_over()
            if over:
                print("\nИГРА ОКОНЧЕНА.")
                print("Проиграл(а): {} (остался(ась) с Ведьмой KS)".format(loser.name))
                winners = [p.name for p in self.players if p is not loser]
                print("Победитель(и): {}".format(", ".join(winners)))
                break

            cur = self.players[self.current_idx]
            print("\nХод: {}".format(cur.name))
            if self.current_idx == 0:
                self._print_state(reveal_human=True)
                raw_input("(Нажмите Enter, чтобы выполнить ход) ")

            self._draw_discard_phase(self.current_idx)

            if cur.can_exchange_now(self.deck):
                self._exchange_phase(self.current_idx)

            self.current_idx = self._next_player_with_cards(self.current_idx)

if __name__ == '__main__':
    WitchGame().run()