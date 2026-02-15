from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from poker.card import Card
from poker.montecarlo import MonteCarloSimulation
from .keyboards import get_suit_keyboard, get_rank_keyboard
from poker.analysis import HandAnalyzer
import time

# Initialize Simulation Engine and Analyzer
simulation = MonteCarloSimulation()
analyzer = HandAnalyzer()

async def format_game_state(user_data):
    """Formats the current game state into a message string."""
    hero = user_data.get('hero', [])
    board = user_data.get('board', [])
    probs = user_data.get('probs', None)
    analysis_text = user_data.get('analysis_text', "")
    
    hero_str = " ".join([str(c) for c in hero]) if hero else "Выберите 2 карты"
    
    board_str = ""
    if board:
        if len(board) >= 3:
            board_str += " ".join([str(c) for c in board[:3]]) # Flop
        if len(board) >= 4:
            board_str += " " + str(board[3]) # Turn
        if len(board) == 5:
            board_str += " " + str(board[4]) # River
    else:
        board_str = "Ожидание..."

    msg = (
        f"<b>🃏 Помощник для Покера</b>\n\n"
        f"<b>👤 Рука Героя:</b> {hero_str}\n"
        f"<b>🎴 Борд:</b> {board_str}\n\n"
    )
    
    if probs:
        msg += (
            f"<b>📊 Вероятности (против 1 случайного оппонента):</b>\n"
            f"🏆 Победа: <code>{probs['win']:.1f}%</code>\n"
            f"🤝 Ничья: <code>{probs['tie']:.1f}%</code>\n"
            f"💀 Поражение: <code>{probs['lose']:.1f}%</code>\n"
            f"📈 Эквити (Equity): <code>{probs['equity']:.1f}%</code>\n\n"
        )

    if analysis_text:
        msg += analysis_text + "\n"
    
    stage = get_current_stage(user_data)
    # Translate stage names
    stage_map = {
        "Hero Card 1": "Карту Героя 1",
        "Hero Card 2": "Карту Героя 2",
        "Flop Card": "Карту Флопа",
        "Turn Card": "Карту Терна",
        "River Card": "Карту Ривера",
        "Result (Game Over)": "Результат (Конец игры)"
    }
    stage_ru = stage_map.get(stage, stage)
    
    msg += f"<i>Текущий шаг: Выберите {stage_ru}</i>\n"
    
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
    context.user_data['probs'] = None
    context.user_data['analysis_text'] = ""
    
    await refresh_message(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a help message."""
    msg = (
        "<b>ℹ️ Справка по боту</b>\n\n"
        "Этот бот помогает рассчитывать вероятности в Техасском Холдеме.\n\n"
        "<b>Как пользоваться:</b>\n"
        "1. Выберите 2 свои карты (Hero).\n"
        "2. Выбирайте карты борда (Флоп, Терн, Ривер).\n"
        "3. Бот автоматически рассчитает ваши шансы на победу против случайной руки.\n\n"
        "<b>Функции:</b>\n"
        "📊 <b>Вероятности</b>: Победа, Ничья, Поражение, Эквити.\n"
        "⚠️ <b>Анализ силы</b>: Бот покажет, какие руки сильнее вашей на текущем борде.\n"
        "🔄 <b>Управление</b>: Кнопки ОТМЕНА (удалить последнюю карту) и СБРОС (начать заново).\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать новую игру\n"
        "/help - Показать это сообщение"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

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
            await query.answer("Все карты выбраны!", show_alert=True)
            return

        user_data['used_cards'].append(str(new_card))
        
        # Trigger Simulation if stage complete
        # Stages: Hero(2), Flop(3 cards on board), Turn(4 cards), River(5 cards)
        # Optimization: Only calculate when a stage is fully complete (0, 3, 4, 5 board cards)
        if len(hero) == 2 and len(board) in [0, 3, 4, 5]:
            await query.edit_message_text("⏳ Расчет вероятностей...", parse_mode='HTML')
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
    # Reduced iterations to prevent timeout/freeze (15k ~ 0.7s)
    probs = simulation.run(hero, board, num_opponents=1, iterations=15000)
    user_data['probs'] = probs

    # Run Stronger Hand Analysis
    stronger_hands = analyzer.analyze_stronger_hands(hero, board)
    formatted = analyzer.format_analysis(stronger_hands)
    
    # If board is present but no stronger hands found -> Hero has Nuts
    if not formatted and len(board) >= 3:
         formatted = "\n<b>💪 У вас сильнейшая рука! (Nuts)</b>\n"
         
    user_data['analysis_text'] = formatted
