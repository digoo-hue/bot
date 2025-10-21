import logging
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
import os
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH

logger = logging.getLogger(__name__)

CHANNELS_FILE = "channels.txt"
SESSION_NAME = "session_scraper"


async def get_posts(limit_per_channel=10):
    """
    Сканирует каналы из channels.txt и возвращает список постов, связанных с выборами в Госдуму 2026.
    """
    posts = []

    api_id = int(TELEGRAM_API_ID)
    api_hash = TELEGRAM_API_HASH

    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    await client.start()

    logger.info("Начинаю сбор постов из каналов...")

    if not os.path.exists(CHANNELS_FILE):
        logger.error("Файл channels.txt не найден!")
        return []

    with open(CHANNELS_FILE, "r") as f:
        channels = [line.strip() for line in f if line.strip()]

    for channel in channels:
        try:
            logger.info(f"📡 Читаю канал {channel}")
            entity = await client.get_entity(channel)
            history = await client(GetHistoryRequest(
                peer=entity,
                limit=limit_per_channel,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))

            for message in history.messages:
                if message.message:
                    posts.append(message.message)

            logger.info(f"✅ {channel}: собрано {len(history.messages)} постов.")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось обработать {channel}: {e}")

    await client.disconnect()

    # 🔍 Фильтрация новостей про выборы
    KEYWORDS = [
        "выборы", "госдума", "депутат", "парламент", "2026",
        "ЦИК", "избиратель", "избирательная кампания", "кандидат", "партия"
    ]

    filtered_posts = [
        post for post in posts
        if any(word.lower() in post.lower() for word in KEYWORDS)
    ]

    logger.info(f"🔎 После фильтрации осталось {len(filtered_posts)} постов про выборы из {len(posts)}.")
    return filtered_posts


if __name__ == "__main__":
    asyncio.run(get_posts())
