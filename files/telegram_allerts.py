import requests  # Для отправки HTTP-запросов к API Telegram и Binance
import time  # Для создания задержек между запросами

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = '---'  # Токен Telegram-бота для отправки уведомлений
TELEGRAM_CHANNEL = '@---'  # ID канала или чата в Telegram (с символом @)
SYMBOL = 'NEARUSDT'  # Торговая пара для мониторинга
LEVEL = 2.965  # Ценовой уровень для отслеживания (при превышении будет отправлено уведомление)

def send_message(text):
    """
    Отправка сообщения в Telegram канал
    
    Args:
        text (str): Текст сообщения для отправки
    
    Returns:
        Response: Объект ответа от API Telegram
    """
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TELEGRAM_TOKEN)
    data = {
        'chat_id': TELEGRAM_CHANNEL,
        'text': text
    }
    response = requests.post(url, data=data) 
    return response


# Основной цикл мониторинга цены
while True:
    # Получаем данные о последней сделке через REST API Binance Futures
    tickers = requests.get(f"https://fapi.binance.com/fapi/v1/trades?symbol={SYMBOL}&limit=1")
    result = tickers.json()  # Преобразуем ответ в JSON формат
    price = result[0]['price']  # Извлекаем цену последней сделки

    # Проверяем, превысила ли цена указанный уровень
    if float(price) > LEVEL:
        # Если превысила - отправляем уведомление с ценой
        text = SYMBOL + '  Price!!! : ' + price
        print(price)  # Выводим цену в консоль
        send_message(text)  # Отправляем в Telegram
    else:
        # Если нет - отправляем сообщение о продолжении поиска
        text = "search"
        send_message(text)
    
    time.sleep(2)  # Пауза 2 секунды между запросами (для избежания превышения лимитов API)