from treys import Deck as TreysDeck, Evaluator, Card as TreysCard
from .card import Card, Deck
from typing import List, Dict

class MonteCarloSimulation:
    def __init__(self):
        self.evaluator = Evaluator()

    def run(self, hero_hand: List[Card], board: List[Card], num_opponents: int = 1, iterations: int = 10000) -> Dict[str, float]:
        """
        Runs a Monte Carlo simulation to calculate equity.
        
        Args:
            hero_hand: List of 2 Card objects for the player.
            board: List of 0, 3, 4, or 5 Card objects.
            num_opponents: Number of opponents (default 1).
            iterations: Number of simulations to run (default 10000).
            
        Returns:
            Dictionary with 'win', 'tie', 'lose', 'equity' percentages.
        """
        if not hero_hand:
             return {'win': 0, 'tie': 0, 'lose': 0, 'equity': 0}

        wins = 0
        ties = 0
        losses = 0

        # Convert our Card objects to treys integers once
        hero_treys = [TreysCard.new(c.to_treys_str()) for c in hero_hand]
        board_treys_orig = [TreysCard.new(c.to_treys_str()) for c in board]

        # Calculate removed cards for deck generation
        removed_treys = hero_treys + board_treys_orig
        
        for _ in range(iterations):
            # Create a fresh treys deck and remove known cards
            deck = TreysDeck()
            # The 'GetDeck' method in treys returns all cards, we need to manually remove known ones
            # But the most efficient way with treys is usually to draw from the deck, 
            # or just shuffle the remaining cards.
            # Treys 'Deck' object has a 'cards' attribute.
            
            # Optimization: Creating a new Deck object every iteration is slow.
            # Instead, we should shuffle a pre-calculated list of remaining cards.
            # For simplicity in this v1, we'll rely on treys.Deck's shuffle mechanids 
            # but getting a "clean" deck and removing cards is expensive.
            # Let's interact with the deck directly.
            
            # Efficient simulation loop:
            # 1. Get remaining cards from a master list
            # 2. Shuffle them
            # 3. Deal to opponents and board
            
            # Re-implementing simplified deck logic for speed
            all_cards = TreysDeck.GetFullDeck()
            remaining_cards = [c for c in all_cards if c not in removed_treys]
            import random
            random.shuffle(remaining_cards)
            
            deck_idx = 0
            
            # Deal opponent hands
            opponents_hands = []
            for _ in range(num_opponents):
                opp_hand = remaining_cards[deck_idx:deck_idx+2]
                deck_idx += 2
                opponents_hands.append(opp_hand)
            
            # Deal remaining board
            current_board = board_treys_orig[:]
            cards_needed = 5 - len(current_board)
            if cards_needed > 0:
                current_board.extend(remaining_cards[deck_idx:deck_idx+cards_needed])
            
            # Evaluate
            hero_score = self.evaluator.evaluate(current_board, hero_treys)
            
            outcome = 'win'
            for opp_hand in opponents_hands:
                opp_score = self.evaluator.evaluate(current_board, opp_hand)
                if opp_score < hero_score:
                    outcome = 'lose'
                    break # Hero lost to at least one opponent
                elif opp_score == hero_score:
                    if outcome != 'lose':
                        outcome = 'tie'
            
            if outcome == 'win':
                wins += 1
            elif outcome == 'tie':
                ties += 1
            else:
                losses += 1

        total = wins + ties + losses
        return {
            'win': (wins / total) * 100,
            'tie': (ties / total) * 100,
            'lose': (losses / total) * 100,
            'equity': ((wins + (ties / 2)) / total) * 100
        }
