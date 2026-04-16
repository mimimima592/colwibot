import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# Берем настройки из переменных окружения (настроим в панели Vercel)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БОТА (та же, что была раньше) ---

@dp.message(F.photo)
async def handle_screenshot(message: types.Message):
    if message.from_user.id == ADMIN_ID: return
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Да", callback_data=f"approve_{message.from_user.id}"),
        types.InlineKeyboardButton(text="❌ Нет", callback_data=f"reject_{message.from_user.id}")
    )
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"От: @{message.from_user.username}",
        reply_markup=builder.as_markup()
    )
    await message.answer("Отправлено на проверку.")

@dp.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def process_decision(callback: types.CallbackQuery):
    action, user_id = callback.data.split("_")
    msg = "✅ Подтверждено!" if action == "approve" else "❌ Отклонено."
    await bot.send_message(int(user_id), msg)
    await callback.message.edit_caption(caption=f"{callback.message.caption}\nСтатус: {action}")
    await callback.answer()

# --- НАСТРОЙКА WEBHOOK ДЛЯ VERCEL ---

async def handle(request):
    if request.method == 'POST':
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return web.Response(text='ok')
    return web.Response(text='Бот запущен')

# Vercel ищет переменную app или handler
app = web.Application()
app.router.add_post('/', handle)
app.router.add_get('/', handle)
