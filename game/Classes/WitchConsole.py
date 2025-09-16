# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import random
from Deck import Deck
from Player import Player
from AIWitch import AIWitch

class WitchGame(object):
    """
    'Ведьма' (K♠ = Witch) — Human vs AI, 36-card deck (6..A).
    """

    def __init__(self, good_prob_human=0.0, good_prob_ai=0.0, seed=None):
        if seed is not None:
            random.seed(seed)
        self.deck = Deck()
        if len(self.deck.cards) not in (36, 35):
            print("Warning: expected a 36-card deck (6..A), got {}".format(len(self.deck.cards)))

        self.player = Player(name='Вы', aces_low=False)
        self.opponent = AIWitch(name='ИИ', aces_low=False, rng=random, epsilon=0.20,
                                reward=1.0, witch_penalty=1.5, decay=0.995, min_trials_boost=0.25)

        # >>> define players list used everywhere
        self.players = [self.player, self.opponent]

        self.good_prob = {0: float(good_prob_human), 1: float(good_prob_ai)}
        self.current_idx = 0

    # ---------- Setup ----------
    def deal_initial(self):
        for i, p in enumerate(self.players):
            p.draw_from_deck(self.deck, trump_suit=None, good_prob=self.good_prob[i])
            p.discard_pairs_excluding_witch()
            p.shaffle_hand()

    # ---------- Utilities ----------
    def _next_player_with_cards(self, start_idx):
        n = len(self.players)
        j = (start_idx + 1) % n
        while j != start_idx and len(self.players[j].hand) == 0:
            j = (j + 1) % n
        return j

    def _game_over(self):
        """
        Game ends ONLY when both players have exactly one card.
        Loser is whoever holds KS.
        """
        a, b = self.players[0], self.players[1]
        if len(a.hand) == 1 and len(b.hand) == 1:
            a_witch = a.has_only_witch()
            b_witch = b.has_only_witch()
            if a_witch and not b_witch:
                return True, a
            if b_witch and not a_witch:
                return True, b
        return False, None

    def _hand_str(self, hand, reveal=True):
        if not hand:
            return '(пусто)'
        if reveal:
            return ' '.join(str(c) for c in hand)
        else:
            return ' '.join('▮' for _ in hand)

    def _print_state(self, reveal_human=True):
        print("\n--- Состояние ---")
        print("Колода: {} карт".format(len(self.deck.cards)))
        print("{}: {}".format(self.players[0].name, self._hand_str(self.players[0].hand, reveal=reveal_human)))
        print("{}: {} [{}]".format(self.players[1].name, self._hand_str(self.players[1].hand, reveal=False), len(self.players[1].hand)))
        print("-----------------")

    # ---------- Turn Phases ----------
    def _draw_discard_phase(self, idx):
        p = self.players[idx]
        return p.draw_up_to_six_and_cleanup(self.deck, good_prob=self.good_prob[idx])

    def _exchange_phase(self, idx):
        cur = self.players[idx]
        nxt_i = self._next_player_with_cards(idx)
        if nxt_i == idx:
            return False
        nxt = self.players[nxt_i]
        if not nxt.hand:
            return False

        if idx == 0:
            # Human chooses an index from AI
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
            # AI (cur) takes from human (nxt) using its strategy
            if hasattr(cur, 'choose_exchange_index'):
                ai_idx = cur.choose_exchange_index(nxt)
            else:
                ai_idx = random.randrange(len(nxt.hand))
            taken = cur.take_card_from(nxt, index=ai_idx, rng=random)
            if hasattr(cur, 'on_after_take'):
                cur.on_after_take(nxt, taken)
            print("\n{} взял одну карту у {}.".format(cur.name, nxt.name))

        # After exchange, both discard pairs and shuffle
        cur.discard_pairs_excluding_witch()
        nxt.discard_pairs_excluding_witch()
        cur.shaffle_hand()
        nxt.shaffle_hand()
        return True

    # ---------- Endgame drain ----------
    def _should_drain(self):
        a, b = self.players[0], self.players[1]
        if len(a.hand) == 0 and len(b.hand) >= 2:
            return 0, 1  # A takes from B
        if len(b.hand) == 0 and len(a.hand) >= 2:
            return 1, 0  # B takes from A
        return None, None

    def _endgame_drain(self):
        while True:
            over, _loser = self._game_over()
            if over:
                return

            taker_idx, donor_idx = self._should_drain()
            if taker_idx is None:
                return

            taker = self.players[taker_idx]
            donor = self.players[donor_idx]
            if not donor.hand:
                return

            print("\nФинишный добор: у {} 0 карт; у {} {} карт.".format(
                taker.name, donor.name, len(donor.hand)
            ))
            if taker_idx == 0:
                # Human chooses which card to take
                print("У {} карт: {} (скрыты)".format(donor.name, len(donor.hand)))
                print("Вид карт: {}".format(self._hand_str(donor.hand, reveal=False)))
                while True:
                    try:
                        choice = raw_input("Выберите индекс карты у {} (1..{}): ".format(donor.name, len(donor.hand)))
                        k = int(choice) - 1
                        if 0 <= k < len(donor.hand):
                            break
                        print("Неверный индекс.")
                    except Exception:
                        print("Введите число.")
                taken = taker.take_card_from(donor, index=k)
                print("Вы взяли: [{}]".format(taken))
            else:
                # AI taker picks using its drain strategy
                if hasattr(taker, 'choose_drain_index'):
                    ai_idx = taker.choose_drain_index(donor)
                else:
                    ai_idx = random.randrange(len(donor.hand))
                taken = taker.take_card_from(donor, index=ai_idx, rng=random)
                if hasattr(taker, 'on_after_take'):
                    taker.on_after_take(donor, taken)
                print("{} взял(а) одну карту у {}.".format(taker.name, donor.name))

            # After each transfer, discard pairs and shuffle
            taker.discard_pairs_excluding_witch()
            donor.discard_pairs_excluding_witch()
            taker.shaffle_hand()
            donor.shaffle_hand()

    # ---------- Post-turn auto top-up with discard/loop ----------
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
                    print(u"Автодобор: {} взял(а) {} карт(ы), теперь {} карт.".format(
                        taker.name, after - before, after
                    ))

            discarded = taker.discard_pairs_excluding_witch()
            if discarded:
                taker.shaffle_hand()

            if self.deck.is_empty():
                break
            if len(taker.hand) == 6 and taker.count_pairs_excluding_witch() == 0:
                break

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

            # Endgame drain after the usual actions
            self._endgame_drain()

            # Post-turn auto top-up with discard/loop
            self._post_turn_balance(self.current_idx)

            self.current_idx = self._next_player_with_cards(self.current_idx)

if __name__ == '__main__':
    WitchGame().run()
