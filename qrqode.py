import qrcode
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application,CommandHandler,ContextTypes,ConversationHandler,CallbackQueryHandler, MessageHandler, filters)
import os

choosecolor, waitdata = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("Создать QR-Код", callback_data="made")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Это бот от qylqa для создания QR-кодов",
    reply_markup = markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "made":
        colors = [
            [InlineKeyboardButton("Черный QR-код на белом фоне", callback_data="black_white")],
            [InlineKeyboardButton("Белый QR-код на черном фоне", callback_data="white_black")],
            [InlineKeyboardButton("Красный QR-код на белом фоне", callback_data="red_white")],
            [InlineKeyboardButton("Желтый QR-код на черном фоне", callback_data="yellow_black")],
            [InlineKeyboardButton("Черный QR-код на синем фоне", callback_data="black_blue")]
        ]
        reply_markup = InlineKeyboardMarkup(colors)

        await query.edit_message_text("Выбери цветовую схему для своего QR-кода",
        reply_markup=reply_markup)
        return choosecolor
    return ConversationHandler.END

async def colorselected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    selected = query.data
    context.user_data['color_scheme'] = selected

    await query.edit_message_text("Хороший выбор, теперь пришли ссылку для QR-кода:")

    return waitdata

async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = update.message.text.strip()

    if not data:
        await update.message.reply_text("Пусто,пришли текст")
        return waitdata
    
    scheme = context.user_data.get("color_scheme", "black_white")

    color_map = {
        "black_white": ("black", "white"),
        "white_black": ("white", "black"),
        "red_white": ("red", "white"),
        "yellow_black": ("yellow", "black"),
        "black_blue": ("black", "blue"),
    }

    fill_color, back_color = color_map.get(scheme, ("black",'white'))

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color,back_color=back_color)

        filename = "qr.png"
        img.save(filename)

        await update.message.reply_photo(
            photo=open(filename, "rb"),
            caption="Вот твой QR-код"
        )

        os.remove(filename)

    except Exception as e:
        await update.message.reply_text("Ошибка!")
        return waitdata


    if "color_scheme" in context.user_data:
        del context.user_data['color_scheme']

    again_keyboard = [[InlineKeyboardButton("Создать еще?", callback_data="made")]]
    again_markup = InlineKeyboardMarkup(again_keyboard)

    await update.message.reply_text("Работа завершена!", reply_markup=again_markup)

    context.user_data.clear()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Отменено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Создать QR", callback_data="made")]]))
    return ConversationHandler.END

def main():
    app = Application.builder().token("TOKEN").build()

    conv = ConversationHandler(entry_points=[CallbackQueryHandler(button,pattern="^made$")],
    states={choosecolor: [CallbackQueryHandler(colorselected)],waitdata:[MessageHandler(filters.TEXT & ~ filters.COMMAND, receive)],},
    fallbacks = [CommandHandler("cancel", cancel)])

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("Бот пахает")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()