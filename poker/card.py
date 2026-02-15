import random
from typing import List, Optional

# Constants for suits and ranks
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}

class Card:
    def __init__(self, rank: str, suit: str):
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank}{self.suit}"

    def __eq__(self, other):
        return isinstance(other, Card) and self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))
    
    def to_treys_str(self) -> str:
        """Converts to treys string format (e.g., 'Ah' for Ace of Hearts)."""
        # Treys expects: '2c', 'As', 'Th', 'Kd'
        # Our suits: ♠ -> s, ♥ -> h, ♦ -> d, ♣ -> c
        suit_map = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
        return f"{self.rank}{suit_map[self.suit]}"

class Deck:
    def __init__(self):
        self.cards: List[Card] = [Card(r, s) for s in SUITS for r in RANKS]
        self.shuffled = False

    def shuffle(self):
        random.shuffle(self.cards)
        self.shuffled = True

    def deal(self, n: int = 1) -> List[Card]:
        if n > len(self.cards):
            raise ValueError("Not enough cards in deck")
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt

    def remove(self, cards_to_remove: List[Card]):
        """Removes specific cards from the deck (e.g., user selected cards)."""
        self.cards = [c for c in self.cards if c not in cards_to_remove]

    def __len__(self):
        return len(self.cards)
