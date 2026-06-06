import os
import asyncio
import random
from threading import Thread

from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7837011810"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@StarStoreUA")

BANK_NAME = "А-Банк"
CARD_NUMBER = "4323 3473 5653 0466"
SUPPORT_LINK = "https://t.me/Artemwesh"

app = Flask(__name__)

@app.route("/")
def home():
    return "Star Store bot is running ✅"

def run_site():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_site, daemon=True).start()

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

orders = {}
waiting_username = {}

PACKS = {
    "50": ("50 звёзд", "60 грн"),
    "100": ("100 звёзд", "90 грн"),
    "200": ("200 звёзд", "190 грн"),
    "500": ("500 звёзд", "450 грн"),
    "1000": ("1000 звёзд", "900 грн"),
    "2000": ("2000 звёзд", "1800 грн"),
    "5000": ("5000 звёзд", "4250 грн"),
    "10000": ("10000 звёзд", "8500 грн"),
}

def make_order_id():
    return f"#STAR{random.randint(1000, 9999)}"

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌟 Купить звёзды", callback_data="buy_stars")],
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
            InlineKeyboardButton(text="💬 Поддержка", callback_data="support")
        ],
        [InlineKeyboardButton(text="🛡️ Гарантия", callback_data="guarantee")]
    ])

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в <b>Star Store</b>!\n\n"
        "Здесь вы можете быстро купить звёзды 🌟",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    await call.message.edit_text(
        "👋 Добро пожаловать в <b>Star Store</b>!\n\n"
        "Здесь вы можете быстро купить звёзды 🌟",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "buy_stars")
async def buy_stars(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="50 звёзд — 60 грн", callback_data="pack_50")],
        [InlineKeyboardButton(text="100 звёзд — 90 грн", callback_data="pack_100")],
        [InlineKeyboardButton(text="200 звёзд — 190 грн", callback_data="pack_200")],
        [InlineKeyboardButton(text="500 звёзд — 450 грн", callback_data="pack_500")],
        [InlineKeyboardButton(text="1000 звёзд — 900 грн", callback_data="pack_1000")],
        [InlineKeyboardButton(text="2000 звёзд — 1800 грн", callback_data="pack_2000")],
        [InlineKeyboardButton(text="5000 звёзд — 4250 грн", callback_data="pack_5000")],
        [InlineKeyboardButton(text="10000 звёзд — 8500 грн", callback_data="pack_10000")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

    await call.message.edit_text(
        "🌟 <b>Выберите пакет звёзд:</b>",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("pack_"))
async def choose_pack(call: CallbackQuery):
    pack_id = call.data.replace("pack_", "")

    if pack_id not in PACKS:
        await call.answer("Пакет не найден", show_alert=True)
        return

    item, price = PACKS[pack_id]

    orders[call.from_user.id] = {
        "order_id": make_order_id(),
        "item": item,
        "price": price,
        "receiver": None,
        "buyer_name": call.from_user.full_name,
        "buyer_username": call.from_user.username,
        "status": "waiting_username"
    }

    waiting_username[call.from_user.id] = True

    await call.message.edit_text(
        "🌟 <b>Куда выдать звёзды?</b>\n\n"
        "Отправьте username получателя.\n\n"
        "Пример:\n"
        "<code>@username</code>\n\n"
        "⚠️ Укажите username внимательно."
    )

@dp.message(F.text.startswith("@"))
async def get_username(message: Message):
    if not waiting_username.get(message.from_user.id):
        return

    user_order = orders.get(message.from_user.id)
    if not user_order:
        await message.answer("❌ Сначала выберите пакет звёзд.")
        return

    receiver = message.text.strip()

    if len(receiver) < 5:
        await message.answer(
            "❌ Username слишком короткий.\n\n"
            "Пример:\n"
            "<code>@username</code>"
        )
        return

    user_order["receiver"] = receiver
    user_order["status"] = "payment"
    waiting_username[message.from_user.id] = False

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_stars")]
    ])

    await message.answer(
        "💳 <b>Оплата переводом на украинскую карту</b>\n\n"
        "<blockquote>"
        f"🧾 <b>Заказ:</b> {user_order['order_id']}\n"
        f"🌟 <b>Товар:</b> {user_order['item']}\n"
        f"👤 <b>Получатель:</b> {receiver}\n"
        f"💰 <b>К оплате:</b> {user_order['price']}"
        "</blockquote>\n\n"

        "🏦 <b>Реквизиты для перевода</b>\n\n"
        "<blockquote>"
        f"• <b>Банк:</b> {BANK_NAME}\n"
        f"• <b>Номер карты:</b> <code>{CARD_NUMBER}</code>\n"
        "• <b>Получатель:</b> Не указан"
        "</blockquote>\n\n"

        "❗ <b>Что нужно сделать</b>\n\n"
        "<blockquote>"
        "1. Переведите точную сумму\n"
        "2. Нажмите кнопку «✅ Я оплатил»\n"
        "3. Отправьте чек оплаты"
        "</blockquote>\n\n"

        "⚠️ <b>Важно</b>\n\n"
        "• Проверьте username перед оплатой\n"
        "• После выдачи изменить получателя нельзя\n\n"

        "🔒 <b>Безопасная сделка</b>\n\n"
        "Все заказы проверяются вручную администратором\n\n"

        "⏳ Обычно проверяем 5–30 минут",
        reply_markup=keyboard
    )

@dp.message(F.text)
async def text_handler(message: Message):
    if waiting_username.get(message.from_user.id):
        await message.answer(
            "❌ Отправьте username в правильном формате.\n\n"
            "Пример:\n"
            "<code>@username</code>"
        )
        return

    text = message.text.strip().upper()
    if text.startswith("#STAR"):
        found_order = None
        for order in orders.values():
            if order.get("order_id", "").upper() == text:
                found_order = order
                break

        if not found_order:
            await message.answer("❌ Заказ не найден.")
            return

        status = found_order.get("status")

        if status == "done":
            status_text = "🟢 Статус:\nУспешно выполнен\n\n🌟 Звёзды успешно выданы."
        elif status == "denied":
            status_text = "🔴 Статус:\nОтклонён\n\n💬 Если возникли вопросы — напишите в поддержку."
        elif status == "pending":
            status_text = "🟡 Статус:\nНа проверке\n\n⏳ Ожидайте решения администратора."
        else:
            status_text = "🟡 Статус:\nОжидает оплаты"

        await message.answer(
            f"🧾 <b>Заказ:</b> <code>{found_order['order_id']}</code>\n\n"
            f"{status_text}"
        )

@dp.callback_query(F.data == "paid")
async def paid(call: CallbackQuery):
    user_order = orders.get(call.from_user.id)

    if not user_order:
        await call.message.answer("❌ Сначала выберите пакет звёзд.")
        return

    if not user_order.get("receiver"):
        await call.message.answer("❌ Сначала укажите username получателя.")
        return

    user_order["status"] = "waiting_check"

    await call.message.answer(
        "📸 <b>Отправьте чек оплаты</b>\n\n"
        "⏳ После отправки чек уйдёт на проверку."
    )

async def send_order_to_admin(message: Message, file_id: str, file_type: str):
    user_order = orders.get(message.from_user.id)

    if not user_order:
        await message.answer("❌ Сначала выберите пакет звёзд.")
        return

    if not user_order.get("receiver"):
        await message.answer("❌ Сначала укажите username получателя.")
        return

    if user_order.get("status") == "pending":
        await message.answer("⏳ Ваш чек уже находится на проверке.")
        return

    user_order["status"] = "pending"

    await message.answer(
        "👀 <b>Чек получен!</b>\n\n"
        "Администратор уже получил ваш заказ.\n\n"
        "⏳ Обычно проверяем 5–30 минут."
    )

    buyer_username = f"@{user_order['buyer_username']}" if user_order["buyer_username"] else "нет username"

    caption = (
        "🚨 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
        f"🧾 Заказ: <code>{user_order['order_id']}</code>\n\n"
        f"👤 Покупатель: <b>{user_order['buyer_name']}</b>\n"
        f"🔗 Username: {buyer_username}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
        f"🌟 Товар: <b>{user_order['item']}</b>\n"
        f"🎯 Выдать на: <b>{user_order['receiver']}</b>\n"
        f"💰 Сумма: <b>{user_order['price']}</b>\n\n"
        "📸 Чек оплаты:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Отказаться", callback_data=f"deny_{message.from_user.id}")
        ]
    ])

    if file_type == "photo":
        await bot.send_photo(
            ADMIN_ID,
            photo=file_id,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await bot.send_document(
            ADMIN_ID,
            document=file_id,
            caption=caption,
            reply_markup=keyboard
        )

@dp.message(F.photo)
async def get_check_photo(message: Message):
    await send_order_to_admin(message, message.photo[-1].file_id, "photo")

@dp.message(F.document)
async def get_check_document(message: Message):
    await send_order_to_admin(message, message.document.file_id, "document")

@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    user_order = orders.get(user_id)

    if not user_order:
        await call.answer("Заказ не найден", show_alert=True)
        return

    user_order["status"] = "done"

    await bot.send_message(
        user_id,
        "🎉 <b>Звёзды успешно выданы!</b>\n\n"
        "🌟 Ваш заказ выполнен.\n"
        "Спасибо за покупку в <b>Star Store</b> 💛"
    )

    if CHANNEL_ID:
        await bot.send_message(
            CHANNEL_ID,
            "✅ <b>Покупатель получил звёзды</b>\n\n"
            f"🧾 <b>Номер заказа:</b> {user_order['order_id']}\n"
            f"🌟 <b>Количество:</b> {user_order['item']}\n"
            "💎 <b>Статус:</b> успешно получено\n\n"
            "🛍️ Спасибо за покупку\n"
            "в <b>Star Store</b>"
        )

    await call.message.edit_caption(
        caption=call.message.caption + "\n\n✅ <b>ОДОБРЕНО</b>"
    )

@dp.callback_query(F.data.startswith("deny_"))
async def deny(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    user_order = orders.get(user_id)

    if not user_order:
        await call.answer("Заказ не найден", show_alert=True)
        return

    user_order["status"] = "denied"

    await bot.send_message(
        user_id,
        "❌ <b>Оплата отклонена</b>\n\n"
        "Чек не прошёл проверку.\n\n"
        "💬 Если возникли вопросы — напишите в поддержку."
    )

    await call.message.edit_caption(
        caption=call.message.caption + "\n\n❌ <b>ОТКАЗАНО</b>"
    )

@dp.callback_query(F.data == "faq")
async def faq(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

    await call.message.edit_text(
        "❓ <b>FAQ / Частые вопросы</b>\n\n"
        "💳 <b>Как купить?</b>\n"
        "— Выберите пакет, укажите username, оплатите и отправьте чек.\n\n"
        "⏳ <b>Сколько ждать?</b>\n"
        "— Обычно 5–30 минут.\n\n"
        "🌟 <b>Куда придут звёзды?</b>\n"
        "— На username, который вы указали.\n\n"
        "📸 <b>Отправил чек — что дальше?</b>\n"
        "— Ожидайте проверки администратора.",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↗️ Написать в поддержку", url=SUPPORT_LINK)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

    await call.message.edit_text(
        "💬 <b>Поддержка</b>\n\n"
        "Если возникли вопросы по оплате, заказу или выдаче звёзд — напишите нам.\n\n"
        "⏳ Обычно отвечаем быстро.",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "guarantee")
async def guarantee(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

    await call.message.edit_text(
        "🛡️ <b>Гарантия Star Store</b>\n\n"
        "🌟 Заказы проверяются вручную\n\n"
        "✅ Звёзды выдаются на указанный username\n\n"
        "💬 Если возникли вопросы — поддержка поможет\n\n"
        "📸 Каждый чек проверяется администратором\n\n"
        "⚠️ Проверяйте username внимательно перед оплатой.",
        reply_markup=keyboard
    )

async def main():
    keep_alive()
    print("Star Store bot started ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
