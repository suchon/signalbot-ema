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
    try:
        #print("In Coin : " + symbols)
        #klines = client.get_historical_klines(symbols, Client.KLINE_INTERVAL_30MINUTE , "120 minutes ago UTC")
        #klines = client.get_historical_klines(symbols, Client.KLINE_INTERVAL_30MINUTE, "860 minutes ago UTC")
        klines = client.get_historical_klines(symbols, Client.KLINE_INTERVAL_1HOUR, "250 hours ago UTC")
        closes = [float(i[4]) for i in klines]
        closes = np.array(closes)
        if len(closes) > 0:
            #ema12 = talib.EMA(closes, timeperiod=12)
            #ema26 = talib.EMA(closes, timeperiod=26)
            ema1 = talib.EMA(closes, timeperiod=50)
            ema2 = talib.EMA(closes, timeperiod=200)
            #cross over/cross under
            for index,data in enumerate(zip(ema1, ema2)):
                e1 = data[0]
                e2 = data[1]
                previous_e1 = ema1[index-1]
                previous_e2 = ema2[index-1]
                # np.isnan(e12) == False and np.isnan(e26) == False and np.isnan(previous_e12) == False and np.isnan(previous_e26) == False:
                if (previous_e1 < previous_e2) and (e1 > e2):
                    #cross over
                    strMessage = "Coine:{} => Signal buy:{}".format(symbols, e2)
                    #print(strMessage)
                    lineNoti.sendtext(strMessage)
                elif (previous_e1 > previous_e2) and (e1 < e2):
                    #cross under
                    strMessage = "Coine:{} => Signal sell:{}".format(symbols, e2)
                    #print(strMessage)
                    lineNoti.sendtext(strMessage)
                else:
                    strMessage = "Coine:{} => Not have Signal".format(symbols)
                    #print(strMessage)
    except Exception as e:
        print("Signal by ema in coin " + symbols + " has error: " + str(e))

def job_scheduler():
    try:
        sched.print_jobs()
        #coin_list = ["BNBUSDT", "CAKEUSDT", "LINAUSDT", "ADAUSDT"]
        #info = client.get_all_tickers()
        #list_coin = [i['symbol'] for i in info]
        #list_coin_usdt = list(filter(lambda x: x.find("USDT") >= 0, list_coin))
        products = client.get_products()
        list_coin_usdt = [x["s"] for x in products["data"] if x['q'] == 'USDT']
        for coin in list_coin_usdt:
            signal_by_ema(coin)
        #signal_by_ema("CAKEUSDT")
        print("-------------------------------------------------")
    except Exception as e:
        print("Job Scheduler error: " + str(e))
        print("-------------------------------------------------")
    

@app.route("/")
def hello_world():
    return "Hello world"

@app.route("/run_check_signel")    
def run_check_signel():
    #products = client.get_products()
    #list_coin_usdt = [x["s"] for x in products["data"] if x['q'] == 'USDT']
    list_coin_usdt = ["BNBUSDT", "CAKEUSDT", "LINAUSDT", "ADAUSDT", "IOSTUSDT", "BTCUSDT"]
    for coin in list_coin_usdt:
        signal_by_ema(coin)
    #signal_by_ema("ADAUSDT")
    return "Hello world : run_check_signel"

@app.route("/check_binance")
def check_binance():
    #Test api binance
    cake = client.get_asset_balance(asset='CAKE')
    return "Binance CAKE : {}".format(cake)

@app.route("/send_line")
def send_line():
    #Test send line
    lineNoti.sendtext("Send Line Test : Hello world")
    return "Hello world"

@app.route("/check_sched")
def check_sched():
    sched_job = ""
    for job in sched.get_jobs():
        sched_job = "Name : {} :: Triger: {} :: NextRunTime : {}".format(job.name, job.trigger, job.next_run_time)
    return "Schedule Job : {}".format(sched_job)

@app.route("/start_sched")    
def start_sched():
    try:
        sched.add_job(job_scheduler,'interval',minutes=60)
        sched.start()
        return "Scheduler is start"
    except Exception as e:
        print("Scheduler Star error: " + str(e))
        return "Scheduler Star error: " + str(e)
   
@app.route("/stop_sched")
def stop_sched():
    try:
        sched.shutdown()
        return "Scheduler is stop"
    except Exception as e:
        print("Scheduler stop error: " + str(e))
        return "Scheduler stop error: " + str(e)
    
if __name__ == "__main__":
    sched.add_job(job_scheduler,'interval',minutes=60)
    sched.start()
    #app.run('127.0.0.1',port=5000)
    #app.run(debug=False)
    app.run()
    