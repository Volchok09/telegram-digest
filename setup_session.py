"""
Одноразовый скрипт для получения Session String.

Запусти ЛОКАЛЬНО на своём компьютере:
  pip install telethon
  python setup_session.py

Скрипт попросит:
  1. Ввести api_id и api_hash (у тебя уже есть)
  2. Ввести номер телефона
  3. Ввести код из Telegram

После этого выведет Session String - длинную строку.
Скопируй её и добавь в GitHub Secrets как TELEGRAM_SESSION_STRING.

ВАЖНО: Session String = доступ к твоему аккаунту!
Никому не показывай и не коммить в репозиторий.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=" * 50)
print("  Генерация Telegram Session String")
print("=" * 50)
print()

api_id = int(input("Введи api_id: "))
api_hash = input("Введи api_hash: ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()
    print()
    print("=" * 50)
    print("  ТВОЙ SESSION STRING (скопируй его):")
    print("=" * 50)
    print()
    print(session_string)
    print()
    print("=" * 50)
    print("  Добавь эту строку в GitHub Secrets")
    print("  как TELEGRAM_SESSION_STRING")
    print("=" * 50)
