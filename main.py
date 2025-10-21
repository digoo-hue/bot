import asyncio
import logging
import re
import html
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config import (
    BOT_TOKEN,
    ADMIN_USER_ID,
    TARGET_CHANNEL_ID,
    SCHEDULE_HOUR,
    SCHEDULE_MIN,
    TZ,
)
from scraper import get_posts
from ai_client import summarize_posts

# -----------------------------------------
# 🔧 ЛОГИРОВАНИЕ
# -----------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Хранилище для черновика
DRAFTS = {}

# -----------------------------------------
# 🪶 HTML форматирование
# -----------------------------------------
def format_html_for_telegram(text: str) -> str:
    if not text:
        return ""

    text = html.escape(text)
    text = re.sub(r"^### (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"^#### (.+)$", r"<i>\1</i>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
    text = re.sub(r"^- (.+)$", r"• \1", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# -----------------------------------------
# 🕒 ПЛАНИРОВЩИК
# -----------------------------------------
async def schedule_task(application):
    tz = pytz.timezone(TZ)
    while True:
        now = datetime.now(tz)
        target_time = tz.localize(datetime(now.year, now.month, now.day, SCHEDULE_HOUR, SCHEDULE_MIN))

        if now > target_time:
            target_time += timedelta(days=1)

        wait_time = (target_time - now).total_seconds()
        logger.info(f"Следующий запуск через {wait_time / 3600:.2f} ч (в {target_time.strftime('%H:%M %Z')})")

        await asyncio.sleep(wait_time)
        await send_news_preview(application.bot)

# -----------------------------------------
# 🧠 ГЕНЕРАЦИЯ ОБЗОРА
# -----------------------------------------
async def send_news_preview(bot):
    logger.info("Начинаю сбор постов из каналов...")
    posts = await get_posts()

    if not posts:
        logger.warning("❗ Постов не найдено — ничего не отправляю.")
        return

    summary = await summarize_posts(posts)
    if not summary:
        logger.error("❌ Ошибка: OpenAI не вернул ответ.")
        return

    formatted_summary = format_html_for_telegram(summary)
    logger.info("✅ Получен ответ от OpenAI, длина текста: %d символов", len(summary))

    keyboard = [
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data="approve"),
            InlineKeyboardButton("❌ Отклонить", callback_data="reject"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        msg = await bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=formatted_summary,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        DRAFTS[msg.message_id] = formatted_summary
        logger.info("Черновик успешно отправлен админу ✅")
    except Exception as e:
        logger.error(f"Ошибка при отправке админу: {e}")

# -----------------------------------------
# 🧭 ОБРАБОТКА КОМАНД
# -----------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для новостных сводок. Команда: /preview")

async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Команда /preview от пользователя {update.effective_user.id}")
    await update.message.reply_text("Генерирую обзор, пожалуйста подожди ⏳...")
    await send_news_preview(context.bot)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg_id = query.message.message_id

    if query.data == "approve":
        logger.info("✅ Админ одобрил публикацию")
        await query.edit_message_text(text="✅ Публикация одобрена. Отправляю в канал...")

        try:
            formatted_text = DRAFTS.get(msg_id)
            if not formatted_text:
                logger.warning("⚠️ Не найден черновик для публикации.")
                return

            await context.bot.send_message(
                chat_id=TARGET_CHANNEL_ID,
                text=formatted_text,
                parse_mode="HTML"
            )
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text="✅ Пост опубликован в канале.")
            logger.info("🎯 Публикация успешно отправлена в канал.")
        except Exception as e:
            logger.error(f"❌ Ошибка публикации в канал: {e}")
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=f"⚠️ Ошибка публикации: {e}")

    elif query.data == "reject":
        logger.info("❌ Админ отклонил публикацию")
        await query.edit_message_text(text="❌ Публикация отклонена.")

# -----------------------------------------
# 🛠️ ОБРАБОТЧИК ОШИБОК
# -----------------------------------------
async def error_handler(update, context):
    logger.error(f"⚠️ Ошибка: {context.error}")
    try:
        if ADMIN_USER_ID:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"⚠️ Ошибка в боте:\n{context.error}"
            )
    except Exception as e:
        logger.error(f"❌ Не удалось уведомить администратора: {e}")

# -----------------------------------------
# 🚀 ЗАПУСК БОТА
# -----------------------------------------
async def start_bot():
    logger.info("Запуск Telegram-бота...")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)

    logger.info("Бот запущен. Начинаю polling и background tasks.")
    asyncio.create_task(schedule_task(application))
    await application.run_polling()

# -----------------------------------------
# ▶️ ОСНОВНОЙ ВХОД
# -----------------------------------------
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(start_bot())
