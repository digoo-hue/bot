import os
import logging
import httpx
import json
from config import AI_API_URL, AI_API_KEY, AI_MODEL

logger = logging.getLogger(__name__)

async def summarize_posts(posts):
    """
    Отправляет новости в OpenRouter и получает краткий тематический обзор выборов в Госдуму 2026.
    """
    if not posts:
        logger.warning("⚠️ Нет постов для анализа.")
        return None

    try:
        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        prompt = (
            "Ты аналитик-политолог. Создай краткий, понятный и объективный обзор новостей, "
            "связанных с выборами в Государственную Думу России 2026 года. "
            "Игнорируй любые новости, не относящиеся к выборам. "
            "Отметь ключевые события, цитаты политиков, решения ЦИК и тенденции кампании. "
            "Пиши в нейтральном журналистском стиле."
        )

        data = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "\n\n".join(posts)},
            ],
            "temperature": 0.6,
            "max_tokens": 1500,
        }

        logger.info(f"🔗 Отправляю запрос в {AI_API_URL}")
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(AI_API_URL, headers=headers, json=data)

        if response.status_code != 200:
            logger.error(f"❌ Ошибка OpenRouter: {response.status_code} - {response.text}")
            return None

        result = response.json()
        summary = result["choices"][0]["message"]["content"].strip()
        logger.info("✅ Сводка успешно создана.")
        return summary

    except Exception as e:
        logger.error(f"❌ Ошибка при обращении к OpenRouter: {e}")
        return None
