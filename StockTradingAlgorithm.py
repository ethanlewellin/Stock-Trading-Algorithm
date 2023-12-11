# -*- coding: utf-8 -*-
"""
Stock Algorithm

@author: Ethan Lewellin
"""
#Import Modules
from datetime import datetime, time
from pytz import timezone

#Functions and Variables from Other Files
from StockScreener import Screen_Stocks
from StockPredictionModel import Predict_Stocks
from TelegramMessenger import send_telegram_message
from TradingRoutine import stockTradingRoutine

now = datetime.now(timezone('EST'))

#Do not run until 7 to get most up to date stock information
while now.time() < time(8,0) and now.time() > time(12,0):
    now = datetime.now(timezone('EST'))
    
#Screen Stocks
ScreenedStocks = Screen_Stocks()

#Train and Run model
stockSummaryDF = Predict_Stocks(tickers=ScreenedStocks)

#Send Message About Stock that will be looked at today
message = str("Stock Program Starting: " + datetime.now().strftime("%B %d, %Y") +'\n' +
              'Looking at ' + str(len(stockSummaryDF)) + ' stocks.' +
              '\n' + 'Tickers: ' + 
              "".join([str(ticker)+', ' for ticker in list(stockSummaryDF['Symbol'])])
              )
send_telegram_message(message=message)
        
#Run Trading Routine
finalDf = stockTradingRoutine(stockSummaryDF=stockSummaryDF)