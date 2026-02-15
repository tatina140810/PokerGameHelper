from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from poker.card import SUITS, RANKS

def get_suit_keyboard():
    """Returns a keyboard with 4 suit buttons."""
    keyboard = [
        [
            InlineKeyboardButton(suit, callback_data=f"suit:{suit}") for suit in SUITS
        ],
        [InlineKeyboardButton("UNDO", callback_data="action:undo"), InlineKeyboardButton("RESET", callback_data="action:reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_rank_keyboard(suit: str, used_cards: list):
    """Returns a keyboard with 13 rank buttons for the selected suit."""
    keyboard = []
    row = []
    for rank in RANKS:
        card_str = f"{rank}{suit}"
        # detailed callback: rank:RANK:SUIT
        callback_data = f"rank:{rank}:{suit}"
        
        # Check if card is already used
        if card_str in used_cards:
            text = " "  # Invisible/Used
            callback_data = "ignore"
        else:
            text = f"{rank}{suit}"
            
        row.append(InlineKeyboardButton(text, callback_data=callback_data))
        
        if len(row) == 4: # 4 buttons per row
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🔙 Back to Suits", callback_data="action:back_to_suits")])
    return InlineKeyboardMarkup(keyboard)
