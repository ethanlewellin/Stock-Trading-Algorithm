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
while now.time() < time(8,0) or now.time() > time(12,0):
    now = datetime.now(timezone('EST'))
    
#Screen Stocks
ScreenedStocks = Screen_Stocks()

print(str(str(len(ScreenedStocks)) + ' Screened stocks.'))

#Train and Run model
SummaryDF = Predict_Stocks(tickers=ScreenedStocks)

#Send Message About Stock that will be looked at today

if len(SummaryDF) > 0: 
    message = str("Stock Program Starting: " + datetime.now().strftime("%B %d, %Y") +'\n' +
                'Looking at ' + str(len(SummaryDF)) + ' stocks.' +
                '\n' + 'Tickers: ' + 
                "".join([str(ticker)+', ' for ticker in list(SummaryDF['Symbol'])])
                )
    send_telegram_message(message=message)
    
    #Run Trading Routine
    finalDf = stockTradingRoutine(stockSummaryDF=SummaryDF)
else: 
    message = str("No stocks with confident predictions today")
    send_telegram_message(message=message)
    
#import pandas as pd
#from TradingRoutine import stockTradingRoutine
#stockTradingRoutine(stockSummaryDF=pd.DataFrame([['SVMH', 1],['NXTP',1]], columns=['Symbol','open']))
