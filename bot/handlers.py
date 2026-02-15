from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from poker.card import Card
from poker.montecarlo import MonteCarloSimulation
from .keyboards import get_suit_keyboard, get_rank_keyboard
import time

# Initialize Simulation Engine
simulation = MonteCarloSimulation()

async def format_game_state(user_data):
    """Formats the current game state into a message string."""
    hero = user_data.get('hero', [])
    board = user_data.get('board', [])
    probs = user_data.get('probs', None)
    
    hero_str = " ".join([str(c) for c in hero]) if hero else "Select 2 cards"
    
    board_str = ""
    if board:
        if len(board) >= 3:
            board_str += " ".join([str(c) for c in board[:3]]) # Flop
        if len(board) >= 4:
            board_str += " " + str(board[3]) # Turn
        if len(board) == 5:
            board_str += " " + str(board[4]) # River
    else:
        board_str = "Waiting..."

    msg = (
        f"<b>🃏 Poker Game Helper</b>\n\n"
        f"<b>👤 Hero Hand:</b> {hero_str}\n"
        f"<b>🎴 Board:</b> {board_str}\n\n"
    )
    
    if probs:
        msg += (
            f"<b>📊 Probabilities (vs 1 Random Opponent):</b>\n"
            f"🏆 Win: <code>{probs['win']:.1f}%</code>\n"
            f"🤝 Tie: <code>{probs['tie']:.1f}%</code>\n"
            f"💀 Lose: <code>{probs['lose']:.1f}%</code>\n"
            f"📈 Equity: <code>{probs['equity']:.1f}%</code>\n\n"
        )
    
    stage = get_current_stage(user_data)
    msg += f"<i>Current Step: Select {stage}</i>\n\n"
    msg += "⚠️ <b>Disclaimer:</b> This tool is for educational purposes only. It does not connect to any poker platform and does not provide real-time assistance."
    
    return msg

def get_current_stage(user_data):
    hero = user_data.get('hero', [])
    board = user_data.get('board', [])
    
    if len(hero) < 2:
        return "Hero Card 1" if len(hero) == 0 else "Hero Card 2"
    elif len(board) < 3:
        return "Flop Card"
    elif len(board) < 4:
        return "Turn Card"
    elif len(board) < 5:
        return "River Card"
    else:
        return "Result (Game Over)"

async def refresh_message(update: Update, context: ContextTypes.DEFAULT_TYPE, markup=None):
    """Updates the message with the current state."""
    text = await format_game_state(context.user_data)
    if markup is None:
        # If no markup provided, default to suit selection (unless game over)
        if get_current_stage(context.user_data) == "Result (Game Over)":
             markup = get_suit_keyboard() # OR reset button only
        else:
             markup = get_suit_keyboard()

    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text=text, reply_markup=markup, parse_mode='HTML')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts a new session."""
    context.user_data.clear()
    context.user_data['hero'] = []
    context.user_data['board'] = []
    context.user_data['used_cards'] = [] # Strings like 'As'
    context.user_data['probs'] = null = None
    
    await refresh_message(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main state machine handler."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_data = context.user_data
    
    # Initialize if empty (in case of restart after long time)
    if 'hero' not in user_data:
        user_data['hero'] = []
        user_data['board'] = []
        user_data['used_cards'] = []

    if data == "ignore":
        return

    if data.startswith("suit:"):
        suit = data.split(":")[1]
        used = user_data.get('used_cards', [])
        # Provide used cards visually to rank keyboard
        # Our used_cards format in user_data matches str(Card)
        # e.g., 'A♠'.
        # But get_rank_keyboard expects checks. The logic needs alignment.
        # Let's align used_cards to store "RankSuit" string (e.g. "A♠")
        await query.edit_message_reply_markup(reply_markup=get_rank_keyboard(suit, used))
        return

    elif data == "action:back_to_suits":
        await query.edit_message_reply_markup(reply_markup=get_suit_keyboard())
        return

    elif data == "action:reset":
        await start_command(update, context)
        return

    elif data == "action:undo":
        # Remove last added card
        board = user_data['board']
        hero = user_data['hero']
        used = user_data['used_cards']
        
        if board:
            popped = board.pop()
            if str(popped) in used: used.remove(str(popped))
        elif hero:
            popped = hero.pop()
            if str(popped) in used: used.remove(str(popped))
        
        # Recalculate if possible
        if len(hero) == 2:
             await run_simulation(user_data)
        else:
             user_data['probs'] = None
             
        await refresh_message(update, context)
        return

    elif data.startswith("rank:"):
        _, rank, suit = data.split(":")
        new_card = Card(rank, suit)
        
        # Determine where to add
        hero = user_data['hero']
        board = user_data['board']
        
        if len(hero) < 2:
            hero.append(new_card)
        elif len(board) < 5:
            # Enforce stage rules? 
            # Request says: Hero(2) -> Flop(3) -> Turn(1) -> River(1)
            # Logic: If 0 in board, need 3? Or just add 1 by 1?
            # User requirement: "Automatically move to the next stage when required cards are selected."
            # "Flop – select 3 cards"
            # It implies we add cards one by one. I will just append to board.
            board.append(new_card)
        else:
            await query.answer("All cards selected!", show_alert=True)
            return

        user_data['used_cards'].append(str(new_card))
        
        # Trigger Simulation if stage complete
        # Stages: Hero(2), Flop(3 cards on board), Turn(4 cards), River(5 cards)
        if len(hero) == 2:
            await query.edit_message_text("⏳ Calculating probabilities...", parse_mode='HTML')
            await run_simulation(user_data)
            
        await refresh_message(update, context)

async def run_simulation(user_data):
    """Runs the simulation and updates user_data['probs']."""
    hero = user_data.get('hero', [])
    board = user_data.get('board', [])
    
    # Needs at least 2 hero cards for any meaningful equity
    if len(hero) < 2:
        return

    # Run Monte Carlo
    # This might block the event loop for 1-2s. For now, we run synchronous.
    # In production, run in run_in_executor.
    probs = simulation.run(hero, board, num_opponents=1, iterations=50000) # User requested 50k
    user_data['probs'] = probs
