import talib
import numpy as np
from flask import Flask
from binance.client import Client
from songline import Sendline
from apscheduler.schedulers.background import BackgroundScheduler
try:
    from config_dev import API_BINANCE_KEY, API_BINANCE_SECRET, API_LINE_TOKEN
except Exception:
    from config_prod import API_BINANCE_KEY, API_BINANCE_SECRET, API_LINE_TOKEN

#+++ Start Connection +++
app = Flask(__name__)
api_key = API_BINANCE_KEY
api_secret = API_BINANCE_SECRET
client = Client(api_key, api_secret)
token = API_LINE_TOKEN
lineNoti = Sendline(token)
sched = BackgroundScheduler(daemon=True)
#+++ End Connection +++

def signal_by_ema(symbols):
    klines = client.get_historical_klines(symbols, Client.KLINE_INTERVAL_30MINUTE , "120 minutes ago UTC")
    closes = [float(i[4]) for i in klines]
    closes = np.array(closes)
    if len(closes) > 0:
        ema12 = talib.EMA(closes, timeperiod=12)
        ema26 = talib.EMA(closes, timeperiod=26)
        #cross over/cross under
        for index,data in enumerate(zip(ema12, ema26)):
            e12 = data[0]
            e26 = data[1]
            previous_e12 = ema12[index-1]
            previous_e26 = ema26[index-1]
            # np.isnan(e12) == False and np.isnan(e26) == False and np.isnan(previous_e12) == False and np.isnan(previous_e26) == False:
            if (previous_e12 < previous_e26) and (e12 > e26):
                #cross over
                strMessage = "Coine:{} => Signal buy:{}".format(symbols, e12)
                #print(strMessage)
                lineNoti.sendtext(strMessage)
            elif (previous_e12 > previous_e26) and (e12 < e26):
                #cross under
                strMessage = "Coine:{} => Signal sell:{}".format(symbols, e12)
                #print(strMessage)
                lineNoti.sendtext(strMessage)
            else:
                strMessage = "Coine:{} => Not have Signal".format(symbols)
                #print(strMessage)
            
            
def job_scheduler():
    sched.print_jobs()
    #coin_list = ["BNBUSDT", "CAKEUSDT", "LINAUSDT", "ADAUSDT"]
    info = client.get_all_tickers()
    list_coin = [i['symbol'] for i in info]
    list_coin_usdt = list(filter(lambda x: x.find("USDT") >= 0, list_coin))
    for coin in list_coin_usdt:
        signal_by_ema(coin)
    print("-------------------------------------------------")

@app.route("/")
def hello_world():
    #info = client.get_all_tickers()
    #list_coin = [i['symbol'] for i in info]
    #list_coin_usdt = list(filter(lambda x: x.find("USDT") >= 0, list_coin))
    #for coin in list_coin_usdt:
    #    signal_by_ema(coin)
    #signal_by_ema("CAKEUSDT")
    return "Hello world"

@app.route("/send_line")
def send_line():
    #Test send line
    lineNoti.sendtext("Send Line Test : Hello world")
    return "Hello world"

@app.route("/start_sched")    
def start_sched():
    sched.add_job(job_scheduler,'interval',minutes=30)
    sched.start()
    return "Scheduler is start"

@app.route("/stop_sched")
def stop_sched():
    sched.shutdown()
    return "Scheduler is stop"

if __name__ == "__main__":
    #app.run('127.0.0.1',port=5000)
    app.run(debug=False)
    