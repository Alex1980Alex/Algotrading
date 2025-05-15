import json
import traceback
import websocket
import threading

class Socket_conn_Binance(websocket.WebSocketApp):
    """
    Класс для работы с WebSocket API Binance.
    Позволяет получать данные в реальном времени (цены, свечи и т.д.)
    
    Наследуется от websocket.WebSocketApp и переопределяет обработчики событий.
    """
    def __init__(self, url):
        """
        Инициализация WebSocket соединения
        
        Args:
            url (str): URL для подключения к WebSocket API Binance
        """
        super().__init__(
            url=url,
            on_open=self.on_open,  # Обработчик события открытия соединения
            on_message=self.on_message,  # Обработчик получения сообщений
            on_error=self.on_error,  # Обработчик ошибок
            on_close=self.on_close  # Обработчик закрытия соединения
        )
        self.run_forever()  # Запуск WebSocket в бесконечном цикле

    def on_open(self, ws):
        """
        Обработчик события открытия соединения
        
        Args:
            ws: WebSocket соединение
        """
        print(ws, 'Websocket was opened')

    def on_error(self, ws, error):
        """
        Обработчик ошибок WebSocket
        
        Args:
            ws: WebSocket соединение
            error: Объект ошибки
        """
        print('on_error', ws, error)
        print(traceback.format_exc())  # Выводим полный стек вызовов для отладки
        exit()  # Завершаем программу при ошибке

    def on_close(self, ws, status, msg):
        """
        Обработчик закрытия соединения
        
        Args:
            ws: WebSocket соединение
            status: Код статуса закрытия
            msg: Сообщение о закрытии
        """
        print('on_close', ws, status, msg)
        exit()  # Завершаем программу при закрытии соединения

    def on_message(self, ws, msg):
        """
        Обработчик получения сообщений от WebSocket сервера
        
        Args:
            ws: WebSocket соединение
            msg: Полученное сообщение
        """
        data = json.loads(msg)  # Преобразуем сообщение из JSON в словарь Python
        # close = data['p']  # Раскомментировать для получения только цены (поле 'p' содержит цену)
        print(data)  # Выводим полученные данные

# URL для подключения к WebSocket потоку торгов ETH/USDT
url = 'wss://stream.binance.com:443/ws/ethusdt@trade'

# Другие варианты URL для разных типов данных:
# url = 'wss://stream.binance.com:443/ws/ethusdt@trade'  # Поток торгов ETH/USDT
# url = 'wss://stream.binance.com:443/ws/ethusdt@kline_1m'  # Поток 1-минутных свечей ETH/USDT
# url = 'wss://stream.binance.com:443/stream?streams=ethusdt@trade/ethusdt@kline_1m'  # Комбинированный поток      
        
# Запускаем WebSocket клиент в отдельном потоке
threading.Thread(target=Socket_conn_Binance, args=(url,)).start()
