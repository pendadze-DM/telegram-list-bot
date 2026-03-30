> Пенда:
import os
import json
import logging
from flask import Flask, request, jsonify
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
# Токен бота берем из переменной окружения (это безопаснее)
TOKEN = os.environ.get('BOT_TOKEN', '8708700124:AAGyRhVVBG_E5GwoTOT9-ZZbtvYyHhee7C8')
# URL, на котором будет висеть бот. Render даст его автоматически.
# Позже мы его укажем в настройках Render.
APP_URL = os.environ.get('APP_URL', 'https://ваш-бот.onrender.com')
WEBHOOK_PATH = '/webhook'  # путь для вебхука
WEBHOOK_URL = f'{APP_URL}{WEBHOOK_PATH}'

# API URL Telegram
TELEGRAM_API_URL = f'https://api.telegram.org/bot{8708700124:AAGyRhVVBG_E5GwoTOT9-ZZbtvYyHhee7C8}'

# Хранилище списков (пока в памяти, для простоты)
# При перезапуске данные сотрутся. Потом можно добавить БД.
user_lists = {}

# Создаем Flask приложение
app = Flask(__name__)

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С TELEGRAM ---
def send_message(chat_id, text):
    """Отправляет сообщение пользователю"""
    url = f'{TELEGRAM_API_URL}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения: {e}")
        return None

def send_start_message(chat_id):
    """Отправляет приветственное сообщение со списком команд"""
    text = (
        "🤖 Привет! Я бот для ведения списка дел или покупок.\n\n"
        "📝 Доступные команды:\n"
        "/add <текст> - добавить элемент в список\n"
        "/list - показать мой список\n"
        "/remove <номер> - удалить элемент по номеру\n"
        "/clear - очистить весь список\n\n"
        "Пример: /add купить молоко"
    )
    send_message(chat_id, text)

def show_user_list(chat_id):
    """Показывает список пользователя"""
    user_id = str(chat_id)
    if user_id not in user_lists or not user_lists[user_id]:
        send_message(chat_id, "📭 Ваш список пуст. Добавьте что-нибудь командой /add")
        return
    
    items = user_lists[user_id]
    text = "📋 <b>Ваш список:</b>\n"
    for idx, item in enumerate(items, start=1):
        text += f"{idx}. {item}\n"
    send_message(chat_id, text)

def add_to_list(chat_id, item_text):
    """Добавляет элемент в список"""
    user_id = str(chat_id)
    if user_id not in user_lists:
        user_lists[user_id] = []
    user_lists[user_id].append(item_text)
    send_message(chat_id, f"✅ Добавлено: {item_text}")

def remove_from_list(chat_id, index_str):
    """Удаляет элемент по номеру"""
    user_id = str(chat_id)
    if user_id not in user_lists or not user_lists[user_id]:
        send_message(chat_id, "Список пуст, нечего удалять.")
        return
    
    try:
        index = int(index_str) - 1
        if index < 0 or index >= len(user_lists[user_id]):
            send_message(chat_id, f"❌ Неверный номер. Используйте /list, чтобы увидеть номера (от 1 до {len(user_lists[user_id])})")
            return
        removed = user_lists[user_id].pop(index)
        send_message(chat_id, f"🗑️ Удалено: {removed}")
    except ValueError:
        send_message(chat_id, "Номер должен быть числом. Пример: /remove 2")

def clear_list(chat_id):
    """Очищает весь список"""
    user_id = str(chat_id)
    if user_id in user_lists:
        user_lists[user_id] = []
    send_message(chat_id, "🧹 Список полностью очищен.")

# --- ОБРАБОТЧИК ВЕБХУКА ---
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Telegram присылает сюда все сообщения"""
    try:
        update = request.get_json()
        if not update:
            return jsonify({'status': 'error', 'message': 'No data'}), 400
        
        logging.info(f"Получен update: {update}")
        
        # Проверяем, есть ли сообщение
        if 'message' not in update:
            return jsonify({'status': 'ok'}), 200
        
        message = update['message']
        chat_id = message['chat']['id']
        
        # Если это текстовое сообщение
        if 'text' in message:

> Пенда:
text = message['text'].strip()
            
            # Разбираем команды
            if text.startswith('/start'):
                send_start_message(chat_id)
            elif text.startswith('/add'):
                # Извлекаем текст после команды
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    send_message(chat_id, "❓ Что добавить? Используйте: /add <текст>")
                else:
                    add_to_list(chat_id, parts[1])
            elif text.startswith('/list'):
                show_user_list(chat_id)
            elif text.startswith('/remove'):
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    send_message(chat_id, "❓ Какой номер удалить? Используйте: /remove <номер>")
                else:
                    remove_from_list(chat_id, parts[1])
            elif text.startswith('/clear'):
                clear_list(chat_id)
            else:
                # Если неизвестная команда
                send_message(chat_id, "❓ Неизвестная команда. Используйте /start для списка команд.")
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logging.error(f"Ошибка в вебхуке: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- ЗДОРОВЬЕ ДЛЯ RENDER ---
@app.route('/health', methods=['GET'])
def health():
    """Render проверяет, жив ли бот"""
    return jsonify({'status': 'healthy'}), 200

# --- НАСТРОЙКА ВЕБХУКА ---
def set_webhook():
    """Устанавливает вебхук при запуске"""
    url = f'{TELEGRAM_API_URL}/setWebhook'
    payload = {'url': WEBHOOK_URL}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Webhook установлен: {WEBHOOK_URL}")
        logging.info(f"Ответ Telegram: {response.json()}")
    except Exception as e:
        logging.error(f"Ошибка установки вебхука: {e}")

# --- ЗАПУСК ---
if name == '__main__':
    # При запуске устанавливаем вебхук
    set_webhook()
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
