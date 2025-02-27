import random
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData
from datetime import datetime, timedelta

# Инициализация бота
API_TOKEN = 'YOUR_BOT_API_TOKEN'  # Укажи свой токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создаем объект для обработки колбэков
game_callback = CallbackData('game', 'action')

# Символы для слотов
SYMBOLS = ['🍒', '🍋', '🍉', '🍊', '🍓', '🍀', '🍇', '⭐', '🔥']
WINNING_COMBINATIONS = {
    '🍒': 5,
    '🍋': 10,
    '🍉': 15,
    '🍊': 20,
    '🍓': 25,
    '🍀': 50,
    '🍇': 100,
    '⭐': 200,
    '🔥': 500,
}
MIN_BET = 100  # Минимальная ставка = 1 монета

# Логгирование ошибок
logging.basicConfig(level=logging.INFO)

# Инициализация базы данных для хранения баланса игрока
players = {}
game_sessions = {}

# Рейтинг игроков по балансу
monthly_ranking = {}

# Колесо фортуны
FORTUNE_WHEEL_REWARDS = [10, 20, 50, 100, 200, -10]  # Рандомные выигрыши или потеря монет
FORTUNE_WHEEL_COST = 0  # Колесо бесплатное, можно изменить на любую цену

# Функция для получения баланса игрока
def get_balance(user_id):
    return players.get(user_id, {'balance': 1000})['balance']

# Функция для обновления баланса игрока
def update_balance(user_id, amount):
    players[user_id] = {'balance': get_balance(user_id) + amount}

# Обновление рейтинга за месяц
def update_monthly_ranking(user_id):
    current_month = datetime.now().strftime('%Y-%m')
    if current_month not in monthly_ranking:
        monthly_ranking[current_month] = []

    player_balance = get_balance(user_id)
    player_name = players.get(user_id, {}).get('name', 'Unknown')
    monthly_ranking[current_month].append((user_id, player_name, player_balance))

# Колесо фортуны
def spin_fortune_wheel():
    return random.choice(FORTUNE_WHEEL_REWARDS)

# Команда для отображения рейтинга
@dp.message_handler(commands=['rating'])
async def show_rating(message: types.Message):
    current_month = datetime.now().strftime('%Y-%m')
    if current_month not in monthly_ranking or not monthly_ranking[current_month]:
        await message.answer("❗️Рейтинг еще не сформирован.")
        return

    # Сортировка по балансу, от большего к меньшему
    sorted_players = sorted(monthly_ranking[current_month], key=lambda x: x[2], reverse=True)

    # Формируем текст с рейтингом
    ranking_text = "🏆 Рейтинг игроков за месяц:\n"
    for idx, (user_id, player_name, player_balance) in enumerate(sorted_players, 1):
        ranking_text += f"{idx}. {player_name} - {player_balance} монет\n"
    
    await message.answer(ranking_text)

# Команда для отображения лучшего игрока
@dp.message_handler(commands=['best_player'])
async def show_best_player(message: types.Message):
    current_month = datetime.now().strftime('%Y-%m')
    if current_month not in monthly_ranking or not monthly_ranking[current_month]:
        await message.answer("❗️Лучший игрок еще не определен.")
        return

    # Сортировка по балансу, от большего к меньшему
    sorted_players = sorted(monthly_ranking[current_month], key=lambda x: x[2], reverse=True)
    
    best_player = sorted_players[0]
    user_id, player_name, player_balance = best_player

    # Показываем лучшего игрока
    await message.answer(f"🏆 Лучший игрок месяца: {player_name} с балансом {player_balance} монет.")

# Проверка, находится ли бот в чате
async def check_if_in_group(message: types.Message):
    if message.chat.type != 'supergroup':
        await message.answer("❗️Пожалуйста, добавьте меня в группу, чтобы начать играть.")
        return False
    return True

# Стартовая команда для запуска игры
@dp.message_handler(commands=['ludic'])
async def start_game(message: types.Message):
    if not await check_if_in_group(message):
        return

    user_id = message.from_user.id
    players[user_id] = {'balance': 1000, 'name': message.from_user.first_name}  # Начальный баланс и имя

    markup = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton("🎰 Слоты", callback_data=game_callback.new(action='slots'))
    button2 = InlineKeyboardButton("🃏 Блэкджек", callback_data=game_callback.new(action='blackjack'))
    button3 = InlineKeyboardButton("🎲 Рулетка", callback_data=game_callback.new(action='roulette'))
    button4 = InlineKeyboardButton("🎉 Колесо фортуны", callback_data=game_callback.new(action='fortune_wheel'))
    markup.add(button1, button2, button3, button4)

    await message.answer(f"Привет, {message.from_user.first_name}! Ваш баланс: {get_balance(user_id)} монет.\n"
                         "Выберите игру:", reply_markup=markup)

# Обработка выбора игры
@dp.callback_query_handler(game_callback.filter())
async def handle_game_selection(callback_query: types.CallbackQuery, callback_data: dict):
    action = callback_data['action']
    user_id = callback_query.from_user.id

    if action == 'slots':
        await slots_menu(callback_query.message, user_id)
    elif action == 'blackjack':
        await blackjack_menu(callback_query.message, user_id)
    elif action == 'roulette':
        await roulette_menu(callback_query.message, user_id)
    elif action == 'fortune_wheel':
        await fortune_wheel(callback_query.message, user_id)

# Меню ставок для игры в слоты
async def slots_menu(message: types.Message, user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton(f"1 монета 💸", callback_data=game_callback.new(action='slots_bet_1'))
    button2 = InlineKeyboardButton(f"5 монет 🤑", callback_data=game_callback.new(action='slots_bet_5'))
    button3 = InlineKeyboardButton(f"10 монет 💰", callback_data=game_callback.new(action='slots_bet_10'))
    button4 = InlineKeyboardButton("🛑 Выйти из игры", callback_data=game_callback.new(action='exit'))
    markup.add(button1, button2, button3, button4)

    await message.answer(f"Ваш баланс: {get_balance(user_id)} монет.\nВыберите ставку для игры в слоты:", reply_markup=markup)

# Генерация слотов (барабаны)
def spin_slots(lines=3):
    result = []
    for _ in range(lines):
        result.append([random.choice(SYMBOLS) for _ in range(3)])  # 3 барабана, 1 линия
    return result

# Подсчет выигрыша
def calculate_win(slots_result):
    win = 0
    for line in slots_result:
        if len(set(line)) == 1:  # Все символы одинаковы
            symbol = line[0]
            win += WINNING_COMBINATIONS.get(symbol, 0)
    return win

# Ставки на слотах
@dp.callback_query_handler(game_callback.filter(action='slots_bet_1'))
async def slots_bet_1(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    bet_amount = 1
    if get_balance(user_id) < bet_amount:
        await callback_query.answer("У вас недостаточно монет для этой ставки.", show_alert=True)
        return

    await callback_query.answer("🔄 Игра началась...")

    # Тайм-аут перед спином, чтобы создать эффект ожидания
    await asyncio.sleep(1)

    slots_result = spin_slots()
    win = calculate_win(slots_result)

    result_text = "🎰 Результат игры:\n"
    for line in slots_result:
        result_text += " | ".join(line) + "\n"
    
    if win > 0:
        result_text += f"✅ Вы выиграли {win} монет!"
        update_balance(user_id, win)
    else:
        result_text += "❌ Вы не выиграли."

    update_monthly_ranking(user_id)
    await callback_query.message.answer(result_text)
    await callback_query.message.answer(f"Ваш новый баланс: {get_balance(user_id)} монет.")

# Обработка выхода из игры
@dp.callback_query_handler(game_callback.filter(action='exit'))
async def exit_game(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()  # Удаление сообщения о текущей игре

    # Показываем финальный баланс
    await callback_query.message.answer(f"Игрок {callback_query.from_user.first_name} покинул игру. Ваш финальный баланс: {get_balance(user_id)} монет.")
    
    # Удаляем из текущей сессии игры
    if user_id in game_sessions:
        del game_sessions[user_id]
