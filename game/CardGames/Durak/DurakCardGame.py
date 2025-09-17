# coding=utf-8
import random

from CardGames.Classes.Card import Card
from CardGames.Classes.Player import Player
from CardGames.Classes.Deck import Deck
from CardGames.Classes.Table import Table
from CardGames.Classes.AIDurak import AIDurak

class DurakCardGame:
    def __init__(self, player_name="Вы", opponent_name="Противник", biased_draw=None):
        self.deck = Deck()
        self.table = Table()
        self.player = Player(player_name)
        self.opponent = AIDurak(opponent_name)
        self.current_turn = None
        self.state = None
        self.result = None

        self.bias = {"player": 0.0, "opponent": 0.0}
        if biased_draw:
            if biased_draw[0] == "player":
                self.bias["player"] = float(biased_draw[1])
            elif biased_draw[0] == "opponent":
                self.bias["opponent"] = float(biased_draw[1])

    def draw_cards(self):
        if not self.deck.cards:
            return

        attacker = self.current_turn or self.player
        defender = self.player if attacker == self.opponent else self.opponent

        def bias_for(p):
            return self.bias["player"] if p == self.player else self.bias["opponent"]

        attacker.draw_from_deck(self.deck, self.deck.trump_suit, good_prob=bias_for(attacker))
        defender.draw_from_deck(self.deck, self.deck.trump_suit, good_prob=bias_for(defender))

    def define_first_turn(self):
        player_trump = self.player.lowest_trump_card(self.deck.trump_suit)
        opponent_trump = self.opponent.lowest_trump_card(self.deck.trump_suit)
        if player_trump and opponent_trump:
            self.current_turn = self.player if not Card.compare_ranks(player_trump.rank, opponent_trump.rank) else self.opponent
        else:
            self.current_turn = random.choice([self.player, self.opponent])
        self.state = "player_attack" if self.current_turn == self.player else "ai_attack"

    def can_attack(self, attacker, num_of_attack_cards=0):
        if len(attacker.hand) == 0:
            return False

        defender = self.player if attacker is self.opponent else self.opponent

        if self.table.num_unbeaten() + num_of_attack_cards > len(defender.hand):
            return False

        if len(self.table) == 0:
            return len(attacker.hand) > 0

        return any(card.rank in self.table.ranks for card in attacker.hand)

    def attack_cards(self, cards):
        if not self.can_attack(self.current_turn, len(cards)):
            return False
        for card in cards:
            if card not in self.current_turn.hand or not self.table.append(card):
                for played_card in cards:
                    if played_card in self.table.table:
                        del self.table.table[played_card]
                        self.table.ranks.discard(played_card.rank)
                return False
        for card in cards:
            self.current_turn.hand.remove(card)
        return True

    def defend_card(self, defend_card, attack_card):
        if not Card.beats(defend_card, attack_card, self.deck.trump_suit):
            return False
        self.player.hand.remove(defend_card)
        self.table.beat(attack_card, defend_card)
        return True

    def ai_attack(self):
        cards = self.opponent.choose_attack_cards(
            self.table,
            self.deck.trump_suit,
            len(self.player.hand)
        )
        if not cards:
            return False

        played = 0
        for card in cards:
            if card in self.opponent.hand and self.table.append(card):
                self.opponent.hand.remove(card)
                played += 1
        return played > 0

    def ai_defend(self):
        for attack_card, (beaten, _) in self.table.table.items():
            if not beaten:
                defend_card = self.opponent.defense(attack_card, self.deck.trump_suit)
                if defend_card:
                    self.opponent.hand.remove(defend_card)
                    self.table.beat(attack_card, defend_card)
                else:
                    return False
        return True

    def throw_ins(self):
        throw_ins = self.opponent.choose_throw_ins(
            self.table,
            len(self.player.hand),
            self.deck.trump_suit
        )
        for card in throw_ins:
            if self.table.append(card):
                self.opponent.hand.remove(card)

    def take_or_discard_cards(self):
        if not self.table.beaten():
            receiver = self.player if self.current_turn != self.player else self.opponent
            receiver.hand.extend(self.table.keys())
            receiver.hand.extend([v[1] for v in self.table.values() if v[1]])
        else:
            self.deck.discard.extend(self.table.keys())
            self.deck.discard.extend([v[1] for v in self.table.values() if v[1]])
            self.current_turn = self.opponent if self.current_turn == self.player else self.player

    def end_turn(self):
        self.opponent.remember_table(self.table)
        self.opponent.remember_discard(self.deck.discard)

        self.table.clear()
        self.draw_cards()

        self.check_endgame()
        self.state = "player_attack" if self.current_turn == self.player else "ai_attack"

    def check_endgame(self):
        if self.deck.cards or (len(self.player.hand) > 0 and len(self.opponent.hand) > 0):
            return
        player_cards = len(self.player.hand)
        opponent_cards = len(self.opponent.hand)
        if player_cards == 0 and player_cards == opponent_cards and self.table.beaten():
            self.result = "draw"
        elif player_cards < opponent_cards:
            self.result = self.player.name
        else:
            self.result = self.opponent.name
