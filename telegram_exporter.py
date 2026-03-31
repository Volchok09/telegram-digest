"""
Telegram Chat Exporter
Вытягивает сообщения из указанных чатов за последние 24 часа
и сохраняет в JSON-файл для последующего анализа.

Использование:
  - Локально: python telegram_exporter.py
  - GitHub Actions: запускается автоматически по расписанию
"""

import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession

# ─── Настройки ───────────────────────────────────────────────
# Эти значения берутся из переменных окружения (GitHub Secrets)
API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION_STRING", "")

# Список чатов для мониторинга
# Можно указать: username (@channel), invite-ссылку, или числовой ID
CHATS = json.loads(os.environ.get("TELEGRAM_CHATS", "[]"))
# Пример: ["@wb_sellers_chat", "@wb_suppliers", -1001234567890]

# За сколько часов назад тянуть сообщения
HOURS_BACK = int(os.environ.get("HOURS_BACK", "24"))

# Куда сохранять результат
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "data")
# ─────────────────────────────────────────────────────────────


async def export_chat(client, chat_id, since):
    """Вытягивает сообщения из одного чата за указанный период."""
    messages = []
    try:
        entity = await client.get_entity(chat_id)
        chat_title = getattr(entity, "title", str(chat_id))

        async for msg in client.iter_messages(entity, offset_date=datetime.now(timezone.utc), reverse=False):
            if msg.date.replace(tzinfo=timezone.utc) < since:
                break
            if msg.text:
                # Получаем имя отправителя
                sender_name = "Unknown"
                if msg.sender:
                    sender_name = getattr(msg.sender, "first_name", "") or ""
                    last = getattr(msg.sender, "last_name", "") or ""
                    if last:
                        sender_name = f"{sender_name} {last}"
                    if not sender_name.strip():
                        sender_name = getattr(msg.sender, "title", str(msg.sender_id))

                messages.append({
                    "id": msg.id,
                    "date": msg.date.isoformat(),
                    "sender": sender_name,
                    "text": msg.text,
                    "reply_to": msg.reply_to_msg_id if msg.reply_to else None,
                    "views": getattr(msg, "views", None),
                })

        print(f"  ✓ {chat_title}: {len(messages)} сообщений")
        return {"chat_id": str(chat_id), "chat_title": chat_title, "messages": messages}

    except Exception as e:
        print(f"  ✗ {chat_id}: ошибка - {e}")
        return {"chat_id": str(chat_id), "chat_title": str(chat_id), "messages": [], "error": str(e)}


async def main():
    if not API_ID or not API_HASH or not SESSION_STRING:
        print("❌ Не заданы переменные окружения TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING")
        return

    if not CHATS:
        print("❌ Не задан список чатов в TELEGRAM_CHATS")
        return

    since = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    print(f"📥 Экспорт сообщений с {since.strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"   Чатов: {len(CHATS)}")

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    results = []
    for chat in CHATS:
        result = await export_chat(client, chat, since)
        results.append(result)

    await client.disconnect()

    # Формируем итоговый файл
    total_msgs = sum(len(r["messages"]) for r in results)
    output = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "period_hours": HOURS_BACK,
        "since": since.isoformat(),
        "total_messages": total_msgs,
        "chats": results,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(OUTPUT_DIR, f"export_{date_str}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Готово! {total_msgs} сообщений сохранено в {filepath}")
    return filepath


if __name__ == "__main__":
    asyncio.run(main())
