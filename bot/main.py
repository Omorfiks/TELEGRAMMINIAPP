import asyncio
import os
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import aiohttp
import json
from utils import upload_photo_to_backend

# Определяем путь к корню проекта (родительская директория от bot/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем переменные окружения: сначала .env, если его нет - .env.example
env_path = BASE_DIR / ".env"
if not env_path.exists():
    env_path = BASE_DIR / ".env.example"

load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения!")
    print(f"Проверьте файл: {env_path}")
    sys.exit(1)

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5173")

SHOP_NAME = os.getenv("SHOP_NAME", "bro shop")
SHOP_HOURS = os.getenv("SHOP_HOURS", "Пн–Сб: 10:00–20:00, Вс: выходной")
SHOP_ADDRESS = os.getenv("SHOP_ADDRESS", "Ваш адрес магазина")
SHOP_LOCATION_URL = os.getenv("SHOP_LOCATION_URL", "https://yandex.ru/maps/")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Web App кнопка
def get_webapp_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🛍️ Открыть магазин",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]])

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = f"""Привет! Это официальный бот магазина **{SHOP_NAME}** 👕

Здесь ты найдёшь каталог, адрес, часы работы и акции!"""
    
    await message.answer(
        text,
        reply_markup=get_webapp_keyboard(),
        parse_mode="Markdown"
    )

# Команда /catalog
@dp.message(Command("catalog"))
async def cmd_catalog(message: Message):
    await message.answer(
        "📦 Открываю каталог товаров...",
        reply_markup=get_webapp_keyboard()
    )

# Команда /hours
@dp.message(Command("hours"))
async def cmd_hours(message: Message):
    await message.answer(f"🕐 Часы работы:\n\n{SHOP_HOURS}")

# Команда /location
@dp.message(Command("location"))
async def cmd_location(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📍 На карте", url=SHOP_LOCATION_URL)
    ]])
    await message.answer(
        f"📍 Адрес магазина:\n\n{SHOP_ADDRESS}",
        reply_markup=keyboard
    )

# Команда /promo
@dp.message(Command("promo"))
async def cmd_promo(message: Message):
    await message.answer("🎉 Акции и скидки доступны в каталоге товаров!", reply_markup=get_webapp_keyboard())

# Админка
class AddProductStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_sizes = State()

class EditProductStates(StatesGroup):
    waiting_for_field = State()
    waiting_for_value = State()

# Временное хранилище для админ-сессий
admin_sessions = {}

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="✏️ Редактировать товар", callback_data="admin_edit_product")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="admin_help")]
    ])
    
    await message.answer("🛠️ Админ-панель bro shop", reply_markup=keyboard)

@dp.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    admin_sessions[callback.from_user.id] = {}
    await state.set_state(AddProductStates.waiting_for_photo)
    await callback.message.answer("📸 Отправьте фото товара")
    await callback.answer()

@dp.message(AddProductStates.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото")
        return
    
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    
    # Сохраняем путь к фото временно
    admin_sessions[message.from_user.id]["photo_path"] = file_path
    admin_sessions[message.from_user.id]["photo_file_id"] = photo.file_id
    await state.set_state(AddProductStates.waiting_for_name)
    await message.answer("✅ Фото получено!\n\nВведите название товара:")

@dp.message(AddProductStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    admin_sessions[message.from_user.id]["name"] = message.text
    await state.set_state(AddProductStates.waiting_for_price)
    await message.answer("💰 Введите цену (только число):")

@dp.message(AddProductStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        admin_sessions[message.from_user.id]["price"] = price
        await state.set_state(AddProductStates.waiting_for_description)
        await message.answer("📄 Введите описание товара:")
    except ValueError:
        await message.answer("❌ Цена должна быть числом. Попробуйте снова:")

@dp.message(AddProductStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    admin_sessions[message.from_user.id]["description"] = message.text
    admin_sessions[message.from_user.id]["sizes"] = {}
    await state.set_state(AddProductStates.waiting_for_sizes)
    await message.answer(
        "📏 Укажите остатки по размерам.\n"
        "Формат: `S: 5` (можно отправлять по одному размеру)\n"
        "Когда закончите, отправьте 'Готово'"
    )

@dp.message(AddProductStates.waiting_for_sizes)
async def process_sizes(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "готово":
        # Сохраняем товар через API
        session_data = admin_sessions[message.from_user.id]
        
        # Загружаем фото на бэкенд
        photo_url = await upload_photo_to_backend(
            session_data["photo_file_id"],
            BOT_TOKEN,
            BACKEND_URL
        )
        
        if not photo_url:
            await message.answer("❌ Ошибка загрузки фото. Попробуйте снова.")
            return
        
        # Создаём товар через API
        product_data = {
            "name": session_data["name"],
            "price": session_data["price"],
            "description": session_data.get("description", ""),
            "image_url": photo_url,
            "sizes": session_data["sizes"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/admin/products",
                json=product_data
            ) as resp:
                if resp.status == 200:
                    await message.answer("✅ Товар добавлен!")
                else:
                    await message.answer("❌ Ошибка при добавлении товара")
        
        await state.clear()
        del admin_sessions[message.from_user.id]
        return
    
    # Парсим размер
    try:
        parts = message.text.split(":")
        if len(parts) != 2:
            raise ValueError
        size = parts[0].strip().upper()
        quantity = int(parts[1].strip())
        admin_sessions[message.from_user.id]["sizes"][size] = quantity
        await message.answer(f"✅ Размер {size}: {quantity} шт. сохранён\n\nОтправьте следующий размер или 'Готово'")
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Используйте: `S: 5`")

@dp.callback_query(F.data == "admin_edit_product")
async def admin_edit_product_start(callback: CallbackQuery):
    # Получаем список товаров
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/api/admin/products") as resp:
            if resp.status == 200:
                products = await resp.json()
                if not products:
                    await callback.message.answer("📦 Товары не найдены")
                    await callback.answer()
                    return
                
                keyboard_buttons = []
                for product in products[:10]:  # Показываем последние 10
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=product["name"],
                            callback_data=f"edit_product_{product['id']}"
                        )
                    ])
                keyboard_buttons.append([
                    InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")
                ])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
                await callback.message.answer("Выберите товар для редактирования:", reply_markup=keyboard)
            else:
                await callback.message.answer("❌ Ошибка получения списка товаров")
    
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_product_"))
async def admin_edit_product_menu(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[-1])
    
    # Получаем товар
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/api/products/{product_id}") as resp:
            if resp.status == 200:
                product = await resp.json()
                
                sizes_text = ", ".join([f"{k}: {v}" for k, v in product.get("sizes", {}).items()])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🖼 Изменить фото", callback_data=f"edit_field_{product_id}_photo")],
                    [InlineKeyboardButton(text="🔤 Название", callback_data=f"edit_field_{product_id}_name")],
                    [InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_field_{product_id}_price")],
                    [InlineKeyboardButton(text="📄 Описание", callback_data=f"edit_field_{product_id}_description")],
                    [InlineKeyboardButton(text="📏 Остатки по размерам", callback_data=f"edit_field_{product_id}_sizes")],
                    [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
                ])
                
                text = f"""Редактирование: "{product['name']}"

💰 Цена: {product['price']} ₽
📏 Размеры: {sizes_text if sizes_text else 'не указаны'}"""
                
                await callback.message.answer(text, reply_markup=keyboard)
            else:
                await callback.message.answer("❌ Товар не найден")
    
    await callback.answer()

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/api/stats") as resp:
            if resp.status == 200:
                stats = await resp.json()
                text = f"📊 Статистика:\n\n"
                text += f"Всего товаров: {stats['total_products']}\n\n"
                text += "ТОП-5 просматриваемых:\n"
                for i, product in enumerate(stats['top_products'], 1):
                    text += f"{i}. {product['name']} - {product['views']} просмотров\n"
                text += "\nПоследние 3 товара:\n"
                for product in stats['recent_products']:
                    text += f"• {product['name']}\n"
            else:
                text = "❌ Ошибка получения статистики"
    
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_help")
async def admin_help(callback: CallbackQuery):
    text = """❓ Помощь по админ-панели:

➕ Добавить товар:
1. Нажмите кнопку "Добавить товар"
2. Отправьте фото
3. Введите название, цену, описание
4. Укажите остатки по размерам (S: 5, M: 3 и т.д.)
5. Отправьте "Готово"

✏️ Редактировать товар:
1. Выберите товар из списка
2. Выберите поле для редактирования
3. Введите новое значение

📊 Статистика:
Показывает общее количество товаров, ТОП-5 просматриваемых и последние добавленные товары."""
    
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="✏️ Редактировать товар", callback_data="admin_edit_product")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="admin_help")]
    ])
    await callback.message.answer("🛠️ Админ-панель bro shop", reply_markup=keyboard)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
