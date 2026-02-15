from treys import Evaluator, Card as TreysCard, Deck as TreysDeck
from .card import Card
from typing import List, Dict, Tuple
import itertools

class HandAnalyzer:
    def __init__(self):
        self.evaluator = Evaluator()

    def analyze_stronger_hands(self, hero_hand: List[Card], board: List[Card]) -> Dict[str, List[str]]:
        """
        Identifies opponent hands that are stronger than the hero's hand.
        Returns a dictionary grouping stronger hands by their rank class (e.g., 'Flush': ['AhKh', ...]).
        """
        if not board or len(board) < 3:
            return {}

        # Convert to treys format
        hero_treys = [TreysCard.new(c.to_treys_str()) for c in hero_hand]
        board_treys = [TreysCard.new(c.to_treys_str()) for c in board]

        hero_score = self.evaluator.evaluate(board_treys, hero_treys)
        
        # Get all remaining cards
        all_cards = TreysDeck.GetFullDeck()
        removed_cards = hero_treys + board_treys
        remaining_cards = [c for c in all_cards if c not in removed_cards]

        stronger_hands = {}

        # Iterate through all possible 2-card opponent hands
        for opp_hand_treys in itertools.combinations(remaining_cards, 2):
            opp_hand_list = list(opp_hand_treys)
            opp_score = self.evaluator.evaluate(board_treys, opp_hand_list)

            if opp_score < hero_score: # Lower score is better in treys
                rank_class = self.evaluator.get_rank_class(opp_score)
                rank_name = self.evaluator.class_to_string(rank_class)
                
                # Convert back to readable string
                c1 = TreysCard.int_to_str(opp_hand_list[0])
                c2 = TreysCard.int_to_str(opp_hand_list[1])
                # Fix suit chars for display (treys uses lowercase letters)
                c1 = c1.replace('s', '♠').replace('h', '♥').replace('d', '♦').replace('c', '♣')
                c2 = c2.replace('s', '♠').replace('h', '♥').replace('d', '♦').replace('c', '♣')
                hand_str = f"{c1}{c2}"

                if rank_name not in stronger_hands:
                    stronger_hands[rank_name] = []
                stronger_hands[rank_name].append(hand_str)

        return stronger_hands

    def format_analysis(self, stronger_hands: Dict[str, List[str]]) -> str:
        """Formats the analysis result into a readable string (Russian)."""
        if not stronger_hands:
            return ""

        # Translation map for hand ranks
        rank_translation = {
            "Royal Flush": "Роял Флеш",
            "Straight Flush": "Стрит Флеш",
            "Four of a Kind": "Каре",
            "Full House": "Фулл Хаус",
            "Flush": "Флеш",
            "Straight": "Стрит",
            "Three of a Kind": "Сет/Тройка",
            "Two Pair": "Две Пары",
            "Pair": "Пара",
            "High Card": "Старшая Карта"
        }

        msg = "\n<b>⚠️ Руки сильнее вашей:</b>\n"
        
        # Sort by rank strength (Treys doesn't strictly order keys, but usually we want strongest first)
        # Approximate order:
        order = ["Royal Flush", "Straight Flush", "Four of a Kind", "Full House", "Flush", "Straight", "Three of a Kind", "Two Pair", "Pair", "High Card"]
        
        count = 0
        for rank_name in order:
            if rank_name in stronger_hands:
                hands = stronger_hands[rank_name]
                ru_rank = rank_translation.get(rank_name, rank_name)
                
                # Limit examples to keep message short
                examples = ", ".join(hands[:3]) 
                remaining = len(hands) - 3
                if remaining > 0:
                    examples += f" и еще {remaining}"
                
                msg += f"• <b>{ru_rank}</b>: {examples}\n"
                count += 1
                if count >= 5: # Limit to top 5 categories to avoid spam
                    msg += "...\n"
                    break
        
        return msg
