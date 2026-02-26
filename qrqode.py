import qrcode
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import os

COLORS = {
    "black": {"name": "Чёрный", "hex": "#000000"},
    "white": {"name": "Белый", "hex": "#FFFFFF"},
    "red": {"name": "Красный", "hex": "#FF0000"},
    "green": {"name": "Зелёный", "hex": "#00FF00"},
    "blue": {"name": "Синий", "hex": "#0000FF"},
    "yellow": {"name": "Жёлтый", "hex": "#FFFF00"},
    "cyan": {"name": "Голубой", "hex": "#00FFFF"},
    "magenta": {"name": "Пурпурный", "hex": "#FF00FF"},
    "orange": {"name": "Оранжевый", "hex": "#FFA500"},
    "purple": {"name": "Фиолетовый", "hex": "#800080"},
    "pink": {"name": "Розовый", "hex": "#FFC0CB"},
    "brown": {"name": "Коричневый", "hex": "#A52A2A"},
    "lime": {"name": "Лаймовый", "hex": "#00FF00"},
    "navy": {"name": "Тёмно-синий", "hex": "#000080"},
    "teal": {"name": "Бирюзовый", "hex": "#008080"},
    "olive": {"name": "Оливковый", "hex": "#808000"},
    "maroon": {"name": "Бордовый", "hex": "#800000"},
    "silver": {"name": "Серебристый", "hex": "#C0C0C0"},
    "gray": {"name": "Серый", "hex": "#808080"},
    "violet": {"name": "Светло-розовый", "hex": "#EE82EE"},
    "indigo": {"name": "Индиго", "hex": "#4B0082"},
    "gold": {"name": "Золотой", "hex": "#FFD700"},
    "beige": {"name": "Бежевый", "hex": "#F5F5DC"},
    "coral": {"name": "Коралловый", "hex": "#FF7F50"},
    "turquoise": {"name": "Бирюза", "hex": "#40E0D0"},
}


def color_keyboard(options, row_size = 3):
    keyboard = []
    row = []

    for i, color in enumerate(options, 1):
        row.append(InlineKeyboardButton(COLORS[color]["name"], callback_data=color))
        if i % row_size == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


choosebg, choosecolor, waitdata = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("Создать QR-Код", callback_data="made")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Это бот от qylqa для создания QR-кодов", reply_markup=markup
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "made":
        bg_options = list(COLORS.keys())
        markup = color_keyboard(bg_options, row_size=3)

        await query.message.delete()
        msg = await query.message.chat.send_message(
            "Выбери цвет фона для своего QR-кода:", reply_markup=markup
        )
        context.user_data["message_id"] = msg
        return choosebg


async def colorbgselected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["bg_color"] = query.data

    await query.message.delete()

    return await choose_qr_color(update, context)


async def choose_qr_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qr_options = [
        color for color in COLORS.keys() if color != context.user_data["bg_color"]
    ]
    markup = color_keyboard(qr_options, row_size=3)

    msg = await update.effective_chat.send_message(
        "Выберите цвет QR-кода:", reply_markup=markup
    )
    context.user_data["message_id"] = msg.message_id

    return choosecolor


async def choose_qr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["qr_color"] = query.data
    await query.message.delete()

    msg = await update.effective_chat.send_message(
        "Пришлите текст или ссылку для QR-кода:"
    )
    context.user_data["message_id"] = msg.message_id

    return waitdata


async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = update.message.text.strip()

    if not data:
        await update.message.reply_text("Пусто,пришли текст")
        return waitdata

    ask_id = context.user_data.get("message_id")

    if ask_id:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=ask_id
        )

    fill_color = COLORS[context.user_data["qr_color"]]["hex"]
    back_color = COLORS[context.user_data["bg_color"]]["hex"]

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color)

        filename = "qr.png"
        img.save(filename)

        await update.message.reply_photo(
            photo=open(filename, "rb"), caption="Вот твой QR-код"
        )

        os.remove(filename)

    except Exception as e:
        await update.message.reply_text("Ошибка!")
        return waitdata

    again_keyboard = [[InlineKeyboardButton("Создать еще?", callback_data="made")]]
    again_markup = InlineKeyboardMarkup(again_keyboard)

    await update.message.reply_text("Работа завершена!", reply_markup=again_markup)

    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Отменено",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Создать QR", callback_data="made")]]
        ),
    )
    return ConversationHandler.END


async def global_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Я не понимаю ваше сообщение!")


async def unknown_choose_bg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста выберите цвет для фона!")
    return choosebg


async def unknown_choose_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста выберите цвет для QR-кода!")
    return choosecolor


async def unknown_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста пришлите текст для QR-кода!")
    return waitdata


def main():
    app = (
        Application.builder()
        .token("TOKEN")
        .build()
    )

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="^made$")],
        states={
            choosecolor: [
                CallbackQueryHandler(choose_qr_callback),
                MessageHandler(filters.ALL, unknown_choose_qr),
            ],
            choosebg: [
                CallbackQueryHandler(colorbgselected),
                MessageHandler(filters.ALL, unknown_choose_bg),
            ],
            waitdata: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive),
                MessageHandler(~filters.TEXT, unknown_data),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.ALL, global_unknown))

    print("Бот пахает")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()