"""
Модуль addons_futures.py - вспомогательные функции для алготрейдинга на Binance Futures

Этот файл содержит набор функций для работы с Binance Futures API:
- Управление позициями (открытие, закрытие, проверка наличия)
- Работа с ордерами (создание рыночных, лимитных, стоп-ордеров, тейк-профит)
- Получение рыночных данных (цены, свечи)
- Расчет технических индикаторов (RSI, ATR, SuperTrend, HalfTrend и др.)
- Отправка уведомлений через Telegram
- Логирование операций

Основные группы функций:
1. Управление данными и логирование: send_to_admin_a, get_json_data, init_file_log, write_to_logs
2. Управление позициями: has_opened_position, get_opened_positions, get_opened_position_direction
3. Управление ордерами: create_market_order, create_limit_order, set_take_profit_market_order, set_stop_loss_market_order
4. Получение рыночных данных: get_symbol_price, get_candels
5. Технические индикаторы: RSI, ATR, HA, supertrend, halftrend, WMA, HMA

Модуль использует библиотеку python-binance для взаимодействия с API Binance,
pandas для обработки данных и расчета индикаторов, requests для HTTP-запросов.

Настройки загружаются из файла settings/settings.json
"""

from datetime import datetime  # Для работы с датой и временем
import time  # Для создания задержек и работы с временными метками
import requests  # Для отправки HTTP-запросов (API Telegram)
from pandas import DataFrame  # Для работы с табличными данными
import pandas as pd  # Библиотека для анализа данных
import numpy as np  # Библиотека для математических вычислений
import json  # Для работы с JSON данными

# Импорт API клиента Binance Futures
from binance.um_futures import UMFutures

pd.options.mode.chained_assignment = None  # Отключение предупреждений pandas о копировании данных

# Загрузка настроек из JSON файла
js_f = open('settings/settings.json')
SETTINGS = json.load(js_f)
js_f.close()

# Инициализация клиента Binance Futures с ключами API из настроек
client = UMFutures(key=SETTINGS['API_KEY'], secret=SETTINGS['SECRET_KEY'])


def send_to_admin_a(text):
    """
    Отправка уведомлений администратору через Telegram

    Args:
        text (str): Текст сообщения для отправки
    """
    apiToken = SETTINGS['BOT_TOKEN']  # Токен Telegram бота из настроек
    chatID = SETTINGS['ADMIN_ID']  # ID чата администратора из настроек
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

    try:
        response = requests.post(apiURL, json={'chat_id': chatID, 'text': text})
        print(response.text)
    except Exception as e:
        print(e)


def get_json_data(path):
    json_data = open(path)
    data = json.load(json_data)
    json_data.close()

    return data


def init_file_log():
    f = open("log/log.txt", "a")
    f.write('\n')
    f.write('Start robot time: ' + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    f.write('\n')
    f.close()


init_file_log()


def write_to_logs(string, symbol=''):
    string = str(string)
    if symbol:
        f = open('log/' + str(symbol) + ".txt", "a")
    else:
        f = open("log/log.txt", "a")
    f.write('\n' + datetime.now().strftime("%d.%m.%Y %H:%M:%S") + '\n')
    f.write(string)
    f.write(
        '\n----------------------------------------------------------')
    f.close()


def round_down(x, n):
    return float(str(x)[:int(n)+2])


def is_int(n):
    return int(n) == float(n)


def has_opened_position(SYMBOL):
    """
    Проверка наличия открытой позиции по указанному символу

    Args:
        SYMBOL (str): Торговая пара для проверки

    Returns:
        bool: True, если есть открытая позиция, False в противном случае
    """
    positions = client.account()['positions']  # Получаем все позиции из аккаунта
    for position in positions:
        # Проверяем, соответствует ли позиция указанному символу и имеет ли ненулевой размер
        if position['symbol'] == SYMBOL and float(position['initialMargin']) > 0 and not float(position['positionAmt']) == 0:
            return True
    return False


def get_opened_positions(SYMBOL):
    opened_positions = []

    positions = client.account()['positions']

    for position in positions:
        if position['symbol'] == SYMBOL and float(position['initialMargin']) > 0 and not float(position['positionAmt']) == 0:
            opened_positions.append(position)
    if opened_positions:
        df = DataFrame(opened_positions).iloc[:, :17]
        df.columns = ['symbol', 'initialMargin', 'maintMargin', 'unrealizedProfit', 'positionInitialMargin',
                      'openOrderInitialMargin', 'leverage', 'isolated', 'entryPrice', 'maxNotional', 'positionSide',
                      'positionAmt', 'notional', 'isolatedWallet', 'updateTime', 'bidNotional', 'askNotional']
    else:
        df = DataFrame(opened_positions)
    return df


def get_opened_position_direction(SYMBOL):
    opened_positions = []

    positions = client.account()['positions']

    for position in positions:
        if (position['symbol'] == SYMBOL) and (float(position['initialMargin']) > 0) and not float(position['positionAmt']) == 0:
            opened_positions.append(position)
    try:
        if float(opened_positions[0]['positionAmt']):
            if float(opened_positions[0]['positionAmt']) > 0:
                return 'BUY'
            else:
                return 'SELL'
    except:
        return False

    return False


def get_position_entry_price(symbol):
    if has_opened_position(symbol):
        position = get_opened_positions(symbol).tail(1)
        return float(position['entryPrice'].iloc[0])
    return False


def get_symbol_price(SYMBOL):
    return float(client.ticker_price(symbol=SYMBOL)['price'])


def close_opened_positions_by_market(SYMBOL):
    opened_positions = []
    positions = client.account()['positions']

    for position in positions:
        if position['symbol'] == SYMBOL and float(position['initialMargin']) > 0 and not float(position['positionAmt']) == 0:
            opened_positions.append(position)

    for position in opened_positions:
        if float(position['positionAmt']) > 0:
            write_to_logs(SYMBOL + ' LONG Закрытие текущей сделки по рынку qnt: ' + str(abs(float(position['positionAmt']))), 'close_opened_positions_by_market')
            create_market_order(SYMBOL, 'SELL', abs(float(position['positionAmt'])), True)
        elif float(position['positionAmt']) < 0:
            write_to_logs(SYMBOL + ' SHORT Закрытие текущей сделки по рынку qnt: ' + str(abs(float(position['positionAmt']))), 'close_opened_positions_by_market')
            create_market_order(SYMBOL, 'BUY', abs(float(position['positionAmt'])), True)

    client.cancel_open_orders(symbol=SYMBOL)


def create_market_order(symbol, side, qnt, reduce_only=False):
    if not(qnt == 0):
        if side == 'BUY':
            print(str(symbol) + ' Рыночный ордер BUY ' + str(abs(qnt)))
            write_to_logs(symbol + ' Рыночный ордер BUY ' + str(abs(qnt)), 'create_market_order')
        else:
            print(str(symbol) + ' Рыночный ордер SHORT ' + str(abs(qnt)))
            write_to_logs(symbol + ' Рыночный ордер SHORT ' + str(abs(qnt)), 'create_market_order')
        if reduce_only:
            order = client.new_order(symbol=symbol, side=side, type='MARKET', quantity=abs(qnt), reduceOnly=True)
            send_to_admin_a(symbol + ' Закрытие позиции ' + side + ' ' + str(qnt))
        else:
            order = client.new_order(symbol=symbol, side=side, type='MARKET', quantity=abs(qnt))
            send_to_admin_a(symbol + ' Открытие новой позиции ' + side + ' ' + str(qnt))
        return order
    return False


def create_limit_order(symbol, side, price, qnt):
    if side == 'BUY':
        print(str(symbol) + ' созданна лимитка LONG: ' + str(price) + ' => ' + str(qnt))
        write_to_logs('созданна лимитка LONG: ' + str(price) + ' => ' + str(qnt), symbol)
        try:
            client.new_order(symbol=symbol, side='SELL', type='LIMIT', price=price, quantity=abs(qnt), timeInForce='GTC')
            send_to_admin_a(symbol + ' Установка лимитки LONG: ' + str(price) + ' => ' + str(qnt))
        except Exception as err:
            print(symbol + f" create_limit_order Ошибка: Unexpected " + err.error_message)
            write_to_logs(symbol + f" create_limit_order Ошибка: Unexpected " + err.error_message, 'create_limit_order')
            send_to_admin_a(symbol + f" create_limit_order Ошибка:\n" + err.error_message)
            close_opened_positions_by_market(symbol)
    else:
        print(str(symbol) + ' созданна лимитка SHORT: ' + str(price) + ' => ' + str(qnt))
        write_to_logs('созданна лимитка SHORT: ' + str(price) + ' => ' + str(qnt), symbol)
        try:
            client.new_order(symbol=symbol, side='BUY', type='LIMIT', price=price, quantity=abs(qnt), timeInForce='GTC')
            send_to_admin_a(symbol + ' Установка лимитки SHORT: ' + str(price) + ' => ' + str(qnt))
        except Exception as err:
            print(symbol + f" create_limit_order Ошибка: Unexpected " + err.error_message)
            write_to_logs(symbol + f" create_limit_order Ошибка: Unexpected " + err.error_message, 'create_limit_order')
            send_to_admin_a(symbol + f" create_limit_order Ошибка:\n" + err.error_message)
            close_opened_positions_by_market(symbol)


def set_take_profit_market_order(symbol, side, price):
    print(str(symbol) + ' Установка TakeProfit: ' + str(price))
    write_to_logs('Установка TakeProfit: ' + str(price), symbol)

    try:
        client.new_order(symbol=symbol, side=side, type='TAKE_PROFIT_MARKET', stopPrice=price, closePosition=True)
        send_to_admin_a(symbol + ' установка TakeProfit ' + str(price))
    except Exception as err:
        print(symbol + f" set_take_profit_market_order Ошибка: Unexpected " + err.error_message)
        write_to_logs(symbol + f" set_take_profit_market_order Ошибка: Unexpected " + err.error_message, 'set_take_profit_market_order')
        send_to_admin_a(symbol + f" set_take_profit_market_order Ошибка:\n" + err.error_message)
        close_opened_positions_by_market(symbol)


def set_stop_loss_market_order(symbol, side, price):
    print(str(symbol) + ' Установка StopLoss: ' + str(price))
    write_to_logs('Установка StopLoss: ' + str(price), symbol)

    try:
        client.new_order(symbol=symbol, side=side, type='STOP_MARKET', stopPrice=price, closePosition=True)
        send_to_admin_a(symbol + ' установка Stop Loss ' + str(price))
    except Exception as err:
        print(symbol + f" set_stop_loss_market_order Ошибка: Unexpected " + err.error_message)
        write_to_logs(symbol + f" set_stop_loss_market_order Ошибка: Unexpected " + err.error_message, 'set_take_profit_market_order')
        send_to_admin_a(symbol + f" set_stop_loss_market_order Ошибка:\n" + err.error_message)
        close_opened_positions_by_market(symbol)


def get_symbol_quantity(symbol, leverage, volume_percent, symbol_price, lot_precision):
    for s in client.exchange_info()['symbols']:
        if s['symbol'] == symbol:
            if s['marginAsset']:
                for i in client.balance():
                    if i['asset'] == s['marginAsset']:
                        return round(float(leverage) * (float(i['balance']) / 100 * float(volume_percent)) / symbol_price, lot_precision)


def get_user_balance():
    user_account = client.account()

    return float(user_account['totalWalletBalance']) - float(user_account['totalUnrealizedProfit'])


def close_long_positions(positions):
    for position in positions:
        if float(position['initialMargin']) > 0 and not float(position['positionAmt']) == 0:
            if float(position['positionAmt']) > 0:
                close_opened_positions_by_market(position['symbol'])


def close_short_positions(positions):
    for position in positions:
        if float(position['initialMargin']) > 0 and not float(position['positionAmt']) == 0:
            if float(position['positionAmt']) < 0:
                close_opened_positions_by_market(position['symbol'])


def get_candels(symbol, TM, limit=1500, slice=True):
    klines = client.klines(symbol, TM, limit=limit)
    if slice:
        # print(klines[-1][6])
        # print(time.time() * 1000)
        if klines[-1][6] > time.time() * 1000:
            # print('pop last candle')
            # print(klines[-1])
            klines.pop()
    for i, val in enumerate(klines):
        klines[i][0] = float(klines[i][0])
        klines[i][1] = float(klines[i][1])
        klines[i][2] = float(klines[i][2])
        klines[i][3] = float(klines[i][3])
        klines[i][4] = float(klines[i][4])

    # df = DataFrame(klines).iloc[:, :5]
    # df.columns = ['Time', 'Open', 'High', 'Low', 'Close']
    return klines


def RSI(df, periods=14, ema=True):
    close_delta = df['Close'].diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    if ema == True:
        # Use exponential moving average
        ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
        ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=periods).mean()
        ma_down = down.rolling(window=periods).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi


def HA(df):
    df_close = df._get_value(0, 'Close')
    df_open = df._get_value(0, 'Open')
    df['Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4

    for i in range(0, len(df)):
        if i == 0:
            df._set_value(i, 'Open', ((df_open + df_close) / 2))
        else:
            df._set_value(i, 'Open', ((df._get_value(i - 1, 'Open') + df._get_value(i - 1, 'Close')) / 2))

    df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
    df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)
    return df


def ATR(df, length=14):
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df_n = pd.concat([high_low, high_cp, low_cp], axis=1)
    true_range = np.max(df_n, axis=1)

    return true_range.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def supertrend(df, period=10, atr_multiplier=3):
    h_and_l_2 = (df['High'] + df['Low']) / 2
    df['atr'] = ATR(df, period)
    df['upperband'] = h_and_l_2 + (atr_multiplier * df['atr'])
    df['lowerband'] = h_and_l_2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['Close'][current] > df['upperband'][previous]:
            # df['in_uptrend'][current] = True
            df.__getitem__('in_uptrend').__setitem__(current, True)

        elif df['Close'][current] < df['lowerband'][previous]:
            # df['in_uptrend'][current] = False
            df.__getitem__('in_uptrend').__setitem__(current, False)

        else:
            # df['in_uptrend'][current] = df['in_uptrend'][previous]
            df.__getitem__('in_uptrend').__setitem__(current, df['in_uptrend'][previous])

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                # df['lowerband'][current] = df['lowerband'][previous]
                df.__getitem__('lowerband').__setitem__(current, df['lowerband'][previous])
            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                # df['upperband'][current] = df['upperband'][previous]
                df.__getitem__('upperband').__setitem__(current, df['upperband'][previous])
    return df


def halftrend(df, amplitude=2, deviation=2):
    df['atr'] = ATR(df, 100)
    df['atr2'] = df['atr'] / 2
    df['dev'] = deviation * df['atr2']


    # print(amplitude)
    # print(deviation)


    df['lowPrice'] = df['Low'].rolling(amplitude).min()
    df['highPrice'] = df['High'].rolling(amplitude).max()

    df['highma'] = df['High'].rolling(window=amplitude).mean()
    df['lowma'] = df['Low'].rolling(window=amplitude).mean()

    df['min_high_price'] = 0
    df['max_low_price'] = 0
    df['in_uptrend'] = False

    trend = False
    next_trend = False

    max_low_price = 0
    min_high_price = 9999999
    for current in range(1, len(df.index)):
        previous = current - 1

        if next_trend:
            max_low_price = max(df['lowPrice'][current], max_low_price)

            if df['highma'][current] < max_low_price and df['Close'][current] < df['Low'][previous]:
                trend = True
                next_trend = False
                min_high_price = df['highPrice'][current]

        else:
            min_high_price = min(df['highPrice'][current], min_high_price)

            if df['lowma'][current] > min_high_price and df['Close'][current] > df['High'][previous]:
                trend = False
                next_trend = True
                max_low_price = df['lowPrice'][current]

        # df['in_uptrend'][current] = not trend
        df.__getitem__('in_uptrend').__setitem__(current, not trend)

        # df['min_high_price'][current] = min_high_price
        df.__getitem__('min_high_price').__setitem__(current, min_high_price)

        # df['max_low_price'][current] = max_low_price
        df.__getitem__('max_low_price').__setitem__(current, max_low_price)

    return df


def WMA(df, period):
    return df.rolling(period).apply(lambda x: ((np.arange(period) + 1) * x).sum() / (np.arange(period) + 1).sum(), raw=True)


def HMA(df, period):
    return WMA(WMA(df, period // 2).multiply(2).sub(WMA(df, period)), int(np.sqrt(period)))


def get_symbol_data(symbol):
    min_lot_size = 0
    lot_precision = 0
    price_precision = 0
    min_notional = 0
    symbol_price = float(client.ticker_price(symbol=symbol)['price'])
    for s in client.exchange_info()['symbols']:
        if s['symbol'] == symbol:
            rs = str(float(s['filters'][0]['tickSize']))
            if '1e' in rs:
                price_precision = int(rs[-1])
            else:
                price_precision = int(len(str(float(s['filters'][0]['tickSize'])).split(".")[1]))

            min_lot_size = float(s['filters'][1]['minQty'])
            if is_int(min_lot_size):
                # lot_precision = int(min_lot_size)
                lot_precision = 0
            else:
                try:
                    if '1e' in str(min_lot_size):
                        lot_precision = int(str(min_lot_size)[-1])
                    else:
                        lot_precision = len(str(min_lot_size).split(".")[1])
                except:
                    lot_precision = 0
            min_notional = float(s['filters'][5]['notional'])

            while min_lot_size * symbol_price < min_notional:
                min_lot_size = min_lot_size + float(s['filters'][1]['minQty'])

            min_lot_size = round(min_lot_size, lot_precision)

    return {
        'min_lot_size': min_lot_size,
        'lot_precision': lot_precision,
        'min_notional': min_notional,
        'symbol_price': symbol_price,
        'price_precision': price_precision
    }
