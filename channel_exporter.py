"""
Telegram Channel Exporter
Вытягивает посты из указанных каналов за последние 24 часа
и сохраняет в JSON-файл для последующего анализа.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession

# ─── Настройки ───────────────────────────────────────────────
API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION_STRING", "")

# Список каналов
CHANNELS = json.loads(os.environ.get("TELEGRAM_CHANNELS", "[]"))

# За сколько часов назад тянуть посты
HOURS_BACK = int(os.environ.get("HOURS_BACK", "24"))

# Куда сохранять результат
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "data")
# ─────────────────────────────────────────────────────────────


async def export_channel(client, channel_id, since):
    """Вытягивает посты из одного канала за указанный период."""
    posts = []
    try:
        entity = await client.get_entity(channel_id)
        channel_title = getattr(entity, "title", str(channel_id))
        channel_username = getattr(entity, "username", "") or ""

        async for msg in client.iter_messages(entity, offset_date=datetime.now(timezone.utc), reverse=False):
            if msg.date.replace(tzinfo=timezone.utc) < since:
                break
            if msg.text:
                posts.append({
                    "id": msg.id,
                    "date": msg.date.isoformat(),
                    "text": msg.text,
                    "views": getattr(msg, "views", None),
                    "forwards": getattr(msg, "forwards", None),
                    "replies": msg.replies.replies if msg.replies else 0,
                })

        print(f"  ✓ {channel_title} (@{channel_username}): {len(posts)} постов")
        return {
            "channel_id": str(channel_id),
            "channel_username": channel_username,
            "channel_title": channel_title,
            "posts": posts,
        }

    except Exception as e:
        print(f"  ✗ {channel_id}: ошибка - {e}")
        return {
            "channel_id": str(channel_id),
            "channel_username": "",
            "channel_title": str(channel_id),
            "posts": [],
            "error": str(e),
        }


async def main():
    if not API_ID or not API_HASH or not SESSION_STRING:
        print("❌ Не заданы переменные окружения")
        return

    if not CHANNELS:
        print("❌ Не задан список каналов в TELEGRAM_CHANNELS")
        return

    since = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    print(f"📥 Экспорт постов каналов с {since.strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"   Каналов: {len(CHANNELS)}")

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    results = []
    for channel in CHANNELS:
        result = await export_channel(client, channel, since)
        results.append(result)

    await client.disconnect()

    total_posts = sum(len(r["posts"]) for r in results)
    output = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "period_hours": HOURS_BACK,
        "since": since.isoformat(),
        "total_posts": total_posts,
        "channels": results,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(OUTPUT_DIR, f"channels_{date_str}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Готово! {total_posts} постов сохранено в {filepath}")
    return filepath


if __name__ == "__main__":
    asyncio.run(main())
