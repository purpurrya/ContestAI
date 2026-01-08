import random
from enum import Enum

class Suit(Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class Card:
    def __init__(self,rank,suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return  f"{self.rank.value}{self.suit.value}"

    def __eq__(self,other):
        if not isinstance(other, Card):
            return False

        return self.rank == other.rank and self.suit == other.suit

    def compare_to(self, other):
        if self.rank.value < other.rank.value:
            return -1
        elif self.rank.value > other.rank.value:
            return 1
        else:
            suit_order = {
                Suit.CLUBS: 0,     
                Suit.HEARTS: 2,
                Suit.SPADES: 3  
            } 

        if suit_order[self.suit] < suit_order[other.suit]:
            return -1
        elif suit_order[self.suit] > suit_order[other.suit]:
            return 1
        return 0

    def to_dict(self) -> dict:
        return {
            "rank": self.rank.value,
            "suit": self.suit.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(Rank(data["rank"]), Suit(data["suit"]))

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()

    def reset(self):
        self.cards = [
            Card(rank, suit)
            for suit in Suit
            for rank in Rank
        ]    
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            raise ValueError("Empty deck")
            return self.cards.pop()