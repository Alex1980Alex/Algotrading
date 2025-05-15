"""
Алгоритм автоматической торговли на Binance Futures

Этот скрипт реализует простую торговую стратегию:
1. Находит криптовалюту с наибольшим ростом за 24 часа
2. Отслеживает рост цены (когда предпоследняя свеча выше, чем предшествующая ей)
3. Открывает LONG позицию при подтверждении роста
4. Устанавливает ордера тейк-профит и стоп-лосс для управления рисками

Скрипт использует API Binance Futures и отправляет уведомления в Telegram.
"""

from binance.um_futures import UMFutures  # Библиотека для работы с Binance Futures API
import time  # Для создания задержек между операциями
import requests  # Для отправки HTTP-запросов (Telegram API)


# === ОСНОВНЫЕ НАСТРОЙКИ ===
TELEGRAM_TOKEN = '---'  # Токен Telegram-бота для отправки уведомлений
TELEGRAM_CHANNEL = '---'  # ID канала или чата в Telegram для отправки сообщений
KEY = '---'  # API ключ от аккаунта Binance
SECRET = '---'  # Секретный ключ API Binance
TF = '15m'  # Таймфрейм для анализа (15-минутные свечи)
TP = 0.03  # Процент прибыли для тейк-профита (3%)
SL = 0.01  # Процент убытка для стоп-лосса (1%)
DEPOSIT = 10  # Размер депозита в USDT для торговли

# Инициализация клиента для работы с Binance Futures
client = UMFutures(key=KEY, secret=SECRET)


def send_message(text):
    """
    Отправка сообщения в Telegram канал
    
    Args:
        text (str): Текст сообщения для отправки
    """
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TELEGRAM_TOKEN)
    data = {
        'chat_id': TELEGRAM_CHANNEL,
        'text': text
    }
    response = requests.post(url, data=data)


def get_top_coin():
    """
    Определение монеты с наибольшим ростом за последние 24 часа
    
    Returns:
        str: Символ монеты с наибольшим процентом роста
    """
    data = client.ticker_24hr_price_change()  # Получаем статистику изменения цен за 24 часа
    change = {}
    # Создаем словарь с процентами изменения для каждой монеты
    for i in data:
        change[i['symbol']] = float(i['priceChangePercent'])
    coin = max(change, key=change.get)  # Находим монету с максимальным ростом    
    print(f"Top coin is: {coin}: {change[coin]}")
    send_message(f"Top coin is: {coin}: {change[coin]}")
    return coin


def get_symbol_price(symbol):
    """
    Получение текущей цены монеты
    
    Args:
        symbol (str): Торговая пара (например, 'BTCUSDT')
    
    Returns:
        float: Текущая цена монеты, округленная до 5 знаков
    """
    price = round(float(client.ticker_price(symbol)['price']), 5)
    print(f"Price: {price}")
    send_message(f"Price: {price}")
    return price


def get_close_data(symbol):
    """
    Получение исторических данных о ценах закрытия свечей
    
    Args:
        symbol (str): Торговая пара (например, 'BTCUSDT')
    
    Returns:
        list: Список цен закрытия для последних 1500 свечей
    """
    klines = client.klines(symbol, TF, limit=1500)  # Получаем до 1500 свечей с указанным таймфреймом
    close = []
    for i in klines:
        close.append(float(i[4]))  # Цена закрытия - 5-й элемент в массиве данных свечи (индекс 4)
    return close


def get_trade_volume():
    """
    Расчет объема для торговли на основе заданного депозита
    
    Returns:
        int: Количество монет для покупки, округленное до целого числа
    """
    volume = round(DEPOSIT/get_symbol_price(symbol))  # Делим депозит на текущую цену монеты
    # print(type(volume))
    print(f"Trade volume: {volume}")
    return volume


def open_market_order(symbol, volume):
    """
    Открытие рыночного ордера на покупку (LONG позиция)
    
    Args:
        symbol (str): Торговая пара
        volume (int): Количество монет для покупки
    """
    params = {
        'symbol': symbol,
        'side': 'BUY',  # Направление - покупка
        'type': 'MARKET',  # Тип ордера - рыночный (исполняется по текущей рыночной цене)
        'quantity': volume,  # Объем ордера
    }

    response = client.new_order(**params)  # Создаем новый ордер с указанными параметрами
    print(response)



def open_stop_order(symbol, price, volume):
    """
    Установка стоп-лосс ордера для защиты от больших убытков
    
    Args:
        symbol (str): Торговая пара
        price (float): Цена для активации стоп-ордера
        volume (int): Количество монет для продажи
    """
    params = {
        'symbol': symbol,
        'side': 'SELL',  # Направление - продажа
        'type': 'STOP_MARKET',  # Тип ордера - стоп-маркет (активируется при достижении указанной цены)
        # 'timeInForce': 'GTC',  # Good Till Cancel - ордер активен до отмены
        'stopPrice': price,  # Цена активации стоп-ордера
        'quantity': volume,  # Объем ордера
    }

    response = client.new_order(**params)  # Создаем новый ордер с указанными параметрами
    print(response)


def open_take_profit_order(symbol, price, volume):
    """
    Установка тейк-профит ордера для фиксации прибыли
    
    Args:
        symbol (str): Торговая пара
        price (float): Цена для активации тейк-профита
        volume (int): Количество монет для продажи
    """
    params = {
        'symbol': symbol,
        'side': 'SELL',  # Направление - продажа
        'type': 'TAKE_PROFIT_MARKET',  # Тип ордера - тейк-профит маркет
        # 'timeInForce': 'GTC',  # Good Till Cancel - ордер активен до отмены
        'stopPrice': price,  # Цена активации тейк-профита
        'quantity': volume,  # Объем ордера
    }

    response = client.new_order(**params)  # Создаем новый ордер с указанными параметрами
    print(response)


def get_take_profit_price():
    """
    Расчет цены для тейк-профит ордера
    
    Returns:
        float: Цена тейк-профита (текущая цена + процент TP)
    """
    take_profit_price = round((price * TP + price), 4)  # Текущая цена + процент прибыли
    print(f"Take Profit: {take_profit_price}")
    return take_profit_price



def get_stop_loss_price():
    """
    Расчет цены для стоп-лосс ордера
    
    Returns:
        float: Цена стоп-лосса (текущая цена - процент SL)
    """
    stop_loss_price = round(price - (price * SL), 4)  # Текущая цена - процент убытка
    print(f"Stop Loss: {stop_loss_price}")
    return stop_loss_price    


# === ОСНОВНОЙ КОД ===
# Получаем монету с наибольшим ростом для торговли
symbol = get_top_coin()
# Получаем исторические данные о ценах закрытия
close = get_close_data(symbol)
# Флаг для отслеживания, открыта ли позиция в данный момент
open_position = False


# Основной цикл торговли
while True:
    # Проверяем условие для входа в позицию:
    # 1. Предпоследняя свеча выше предыдущей (рост цены)
    # 2. У нас нет открытой позиции
    if close[-2] > close[-3] and open_position == False:
        print("The coin is growing")
        send_message("The coin is growing")
        
        # Рассчитываем объем для торговли
        volume = get_trade_volume()
        # Получаем текущую цену
        price = get_symbol_price(symbol)
        
        # Открываем рыночный ордер на покупку (LONG позиция)
        open_market_order(symbol, volume)        
        open_position = True  # Устанавливаем флаг, что позиция открыта
        send_message("The position was open")  # Отправляем уведомление
        time.sleep(2)  # Ждем 2 секунды для обработки ордера
        
        # Рассчитываем и устанавливаем уровни тейк-профита и стоп-лосса
        take_profit_price = get_take_profit_price()
        stop_loss_price = get_stop_loss_price()  
             
        # Устанавливаем стоп-лосс ордер
        open_stop_order(symbol, stop_loss_price, volume)
        send_message("The Stop Loss order was set")
        time.sleep(2)  # Ждем 2 секунды для обработки ордера
        
        # Устанавливаем тейк-профит ордер
        open_take_profit_order(symbol, take_profit_price, volume) 
        send_message("The Take Profit order was set") 

    else:
        # Если условия для входа не выполнены, продолжаем мониторинг
        print("The coin is not growing")
        send_message("The coin is not growing")


