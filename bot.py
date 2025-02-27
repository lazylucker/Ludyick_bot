import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from datetime import datetime
import os

API_TOKEN = os.getenv("API_TOKEN")  # Берем токен из переменных окружения
RANKING_FILE = "ranking.json"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Функции работы с рейтингом
def load_ranking():
    try:
        with open(RANKING_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ranking(ranking):
    with open(RANKING_FILE, 'w') as f:
        json.dump(ranking, f)

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Привет! Напиши 'Лудик' в чат, чтобы начать игру!")

# Обработчик "Лудик"
@dp.message_handler(lambda message: message.text.lower() == 'лудик')
async def start_game(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Слот", "Блэкджек", "Рулетка", "Рейтинг", "Колесо Фортуны")
    await message.answer("🎰 Добро пожаловать в Лудик! Выберите игру:", reply_markup=markup)

# Выбор игры
@dp.message_handler(lambda message: message.text in ['Слот', 'Блэкджек', 'Рулетка', 'Колесо Фортуны'])
async def game_choice(message: types.Message):
    game = message.text.lower()
    if game == 'слот':
        await message.answer("🎰 Запускаю слот-машину!")
    elif game == 'блэкджек':
        await message.answer("🃏 Запускаю блэкджек!")
    elif game == 'рулетка':
        await message.answer("🎡 Запускаю рулетку!")
    elif game == 'колесо фортуны':
        await message.answer("🎡 Кручу колесо фортуны!")

# Рейтинг игроков
@dp.message_handler(commands=['rating'])
async def show_rating(message: types.Message):
    ranking = load_ranking()
    current_month = datetime.now().strftime('%Y-%m')

    if current_month not in ranking or not ranking[current_month]:
        await message.answer("❗️ Рейтинг еще не сформирован.")
        return

    sorted_players = sorted(ranking[current_month], key=lambda x: x[2], reverse=True)

    ranking_text = "🏆 Рейтинг игроков за месяц:\n"
    for idx, (user_id, player_name, player_balance) in enumerate(sorted_players, 1):
        ranking_text += f"{idx}. {player_name} - {player_balance} монет\n"

    await message.answer(ranking_text)

# Обновление рейтинга
def update_monthly_ranking(user_id):
    current_month = datetime.now().strftime('%Y-%m')
    ranking = load_ranking()

    if current_month not in ranking:
        ranking[current_month] = []

    player_balance = 100
    player_name = "Игрок"
    ranking[current_month].append((user_id, player_name, player_balance))

    save_ranking(ranking)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
