import ccxt
import talib
import tkinter as tk
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import winsound
import logging
import threading
from PIL import Image, ImageTk
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Flask, render_template
from multiprocessing import Process

app = Flask(__name__)

class TradingBot:
    def __init__(self, symbol, timeframe):
        self.open_positions = []
        self.past_data = []
        self.trading_results = []
        self.symbol = symbol
        self.timeframe = timeframe
        self.api_key = "insert your key"
        self.secret_key = "insert your key"
        self.exchange = "BINANCE"
        self.orders = []
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.current_price = 0.0
        self.pnl = 0
        self.buy = 0
        self.sell = 0
        self.pnl_list = []
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.plot_open_prices = self.figure.add_subplot(121)
        self.plot_pnl = self.figure.add_subplot(122)
        self.canvas = FigureCanvas(self.figure)


    def connect_to_exchange_api(self):
        self.exchange = ccxt.binance({'apiKey': self.api_key, 'secret': self.secret_key})
        print("Connecting to Exchange...")

    def get_real_time_market_info(self):
        print("Getting market data...")
        symbol = self.symbol
        timeframe = self.timeframe
        candles = self.exchange.fetch_ohlcv(symbol, timeframe)
        df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['pnl']= 0.00
        dg = pd.DataFrame(df['pnl'] )
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        rsi = talib.RSI(df['Close'], timeperiod=10)

        # High Cohesion between get_real_time_market_info() and run_strategy()
        action = self.run_strategy(candles)
        if action == 'buy':
            x = 0
            current_rsi = rsi.iloc[-1]

            counter = 0
            for i in range(len(rsi)):
                if current_rsi < 55:
                    current_rsi = rsi[i]
                    x += 1
                    counter += 1
                    if counter >= len(rsi):
                        break
            self.buy += 1
            message = "Buy Order placed..."
            self.current_price = (df['Open']).iloc[-x]

            #Calculating Profit or Loss on the trade

            result = (df['Open']).iloc[-1] - self.current_price
            self.pnl += result
            self.pnl_list.append(self.pnl)
            dg = dg._append({'pnl': self.pnl}, ignore_index=True)
            print(self.pnl_list)

            #Notifying the user

            self.notify_user(message, result, self.pnl)
            print("TRADE RESULT  ======>   ")
            print(result)
            winsound.Beep(500, 5000)

        elif action == 'sell':

            x = 0
            current_rsi = rsi.iloc[-1]
            counter = 0
            for i in range(len(rsi)):
                if current_rsi < 45:
                    current_rsi = rsi[i]
                    x += 1
                    counter += 1
                    if counter >= len(rsi):
                        break

            self.sell += 1
            message = "Sell Order placed..."
            self.current_price = (df['Open']).iloc[-x]

            #Calculating Profit or Loss on the trade

            result = (df['Open']).iloc[-1] - self.current_price
            self.pnl += result
            self.pnl_list.append(self.pnl)
            dg = dg._append({'pnl': self.pnl}, ignore_index=True)

            print(self.pnl_list)

            #Notifying the user

            self.notify_user(message, result, self.pnl)
            print("TRADE RESULT  ======>   ")
            print(result)
            winsound.Beep(500, 3000)

            if action == 'hold':
                print("No trade...")




            '''

            FOR ACTUAL TRADES

            order = self.exchange.create_market_buy_order(symbol, 0.001)
            self.orders.append(order)
            self.notify_user('Bought at ' + str(order['price']))

            FOR ACTUAL TRADES


            if len(self.orders) > 0:
                order = self.exchange.create_market_sell_order(symbol, 0.001)
                profit = (order['price'] - self.orders[-1]['price']) * 0.001
                self.orders.pop()
                self.notify_user('Sold  ' + str(order['price']) + ' for a profit of ' + str(profit))
            '''

    def run_strategy(self, candles):
        print("Executing Strategy...")
        closes = np.array([float(candle[4]) for candle in candles])
        rsi = talib.RSI(closes, timeperiod=2)
        plt.clf()
        plt.plot(rsi)
        plt.title('RSI')
        plt.xlabel('Timestamp')
        plt.ylabel('RSI')
        plt.savefig('static/image/plot.png')
        test = False
        test2 = False
        last_rsi = rsi[-1]
        if last_rsi >= 70:
            for i in range(3):
                if rsi[-i] < 70:
                    test = True
        if (test == True):
            return 'sell'

        elif last_rsi <= 30:
            for i in range(3):
                if rsi[-i] > 70:
                    test2 = True
            if (test2 == True):
                return 'buy'

        else:
            return 'hold'


#not called due to simulated trading
    def place_order(self, order_type, order_amount):
        print("Order Placed...")
        # code to execute for real orders
        '''


            FOR ACTUAL TRADES


        symbol = self.symbol
        if order_type == 'buy':
            side = 'buy'
            params = {'type': 'market', 'timeInForce': 'GTC'}
            amount = order_amount
            price = None
        elif order_type == 'sell':
            side = 'sell'
            params = {}
            amount = order_amount
            price = None  # market sell order
        else:
            raise ValueError('Invalid order type: ' + order_type)

        try:
            order = self.exchange.create_order(symbol, 'market', side, amount, price, params)
            self.orders.append(order)
            self.notify_user(f"{side.capitalize()} order executed for {amount} {symbol.split('/')[0]} at {order['price']}")
        except Exception as e:
            self.notify_user(f"Failed to place {side} order: {e}")
        '''

    def handle_open_positions(self):
        symbol = self.symbol
        open_orders = self.exchange.fetch_open_orders(symbol)
        print("Handling open positions...")

        for order in open_orders:
            if order['type'] == 'limit':
                order_type = 'buy' if order['side'] == 'buy' else 'sell'
                order_price = order['price']
                order_amount = order['amount']
                if order_type == 'buy':
                    stop_price = order_price * (1 - self.stop_loss)
                    take_price = order_price * (1 + self.take_profit)
                else:
                    stop_price = order_price * (1 + self.stop_loss)
                    take_price = order_price * (1 - self.take_profit)

                # check stop loss
                print("Checking any stop loss orders... ")
                current_price = self.exchange.fetch_ticker(symbol)['last']
                if order_type == 'buy' and current_price < stop_price:
                    self.exchange.cancel_order(order['id'], symbol=symbol)
                    self.notify_user(f"Buy order at {order_price} stopped out at {current_price}")
                elif order_type == 'sell' and current_price > stop_price:
                    self.exchange.cancel_order(order['id'], symbol=symbol)
                    self.notify_user(f"Sell order at {order_price} stopped out at {current_price}")

                # check take profit

                elif order_type == 'buy' and current_price > take_price:
                    print("Checking any take profit orders... ")
                    self.exchange.cancel_order(order['id'], symbol=symbol)
                    profit = order_amount * (current_price - order_price)
                    self.trading_results.append(profit)
                    self.notify_user(f"Buy order at {order_price} closed at {current_price} for a profit of {profit}")
                elif order_type == 'sell' and current_price < take_price:
                    self.exchange.cancel_order(order['id'], symbol=symbol)
                    profit = order_amount * (order_price - current_price)
                    self.trading_results.append(profit)
                    self.notify_user(f"Sell order at {order_price} closed at {current_price} for a profit of {profit}")

    def notify_user(self, message, result, pnl):
        print(message)

        with open("orders.log", "a") as f:
            f.write(message)
            f.write("-------------->  THE Trade Result Is {:.2f}".format(result))
            f.write("\n")
            f.write("PnL --------------> {:.2f}".format(pnl))
            f.write("\n")


    def run(self):
        self.is_running = True
        while self.is_running:
            self.connect_to_exchange_api()
            self.get_real_time_market_info()
            self.handle_open_positions()
            time.sleep(60)  # For stabilty as API closes connection if the requests are too frequent




def run_trading_bot():
    bot = TradingBot("BTC/USDT", "1s")
    bot.run()
def app_runner():
    app.run(debug=True,port=9000)

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    trader = Process(target=run_trading_bot)
    trader.start()
    app.run( port=9000)
    trader.join()


