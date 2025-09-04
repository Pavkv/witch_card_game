# coding=utf-8
class Card:
    suits = ['C', 'D', 'H', 'S'] # C for Clubs(Крести/Трефы), D for Diamonds(Бубны), H for Hearts(Черви), S for Spades(Пики)
    # '2', '3', '4', '5',
    ranks = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] # J for Jack(Валет), Q for Queen(Дама), K for King(Король), A for Ace(Туз)
    rank_values = {rank: i for i, rank in enumerate(ranks)}
    points21_map = {
        '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 2, 'Q': 3, 'K': 4, 'A': 11
    }
    WITCH_RANK = 'K'
    WITCH_SUIT = 'S'

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return "{}{}".format(self.rank, self.suit)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, Card) and self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))

    def is_good_card(self, trump_suit):
        return self.suit == trump_suit or Card.rank_values[self.rank] >= Card.rank_values['9']

    @classmethod
    def compare_ranks(cls, rank1, rank2):
        return cls.rank_values[rank1] > cls.rank_values[rank2]

    @classmethod
    def beats(cls, defender, attacker, trump):
        if defender.suit == attacker.suit:
            return cls.rank_values[defender.rank] > cls.rank_values[attacker.rank]
        elif defender.suit == trump and attacker.suit != trump:
            return True
        else:
            return False

    def points21(self):
        return Card.points21_map[self.rank]

    def is_witch(self):
        return self.rank == Card.WITCH_RANK and self.suit == Card.WITCH_SUIT

    @classmethod
    def is_witch_card(cls, card):
        """Class helper for arbitrary card objects."""
        return isinstance(card, Card) and card.rank == cls.WITCH_RANK and card.suit == cls.WITCH_SUIT