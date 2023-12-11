# -*- coding: utf-8 -*-
"""
Stock Trading Routine

@author: ethan
"""

#Imports
import pandas as pd
import yfinance as yf
from datetime import datetime, time
from pytz import timezone
from collections import Counter
import statistics

from Variables import RSI_UNDERSOLD, REL_VOL_UPPER, PERCENT_B_Lower, RSI_OVERSOLD, REL_VOL_LOWER, PERCENT_B_UPPER, INCREASE_LOW, INCREASE_HIGH, LAST_BUY_TIME, STOPLOSS, check_condition
from TelegramMessenger import send_telegram_message

def stockTradingRoutine(stockSummaryDF):
    historyDfList = []
    for symbol in stockSummaryDF['Symbol']:
        tempList=yf.download(tickers=symbol, period="5d", interval="1m",progress=False)['Close'][::-1].to_list()[:60]
        tempList=tempList[::-1]
        tempList.insert(0,symbol)
        historyDfList.append(tempList)
        
    historyDF = pd.DataFrame(historyDfList)
    historyDF = historyDF.set_index(0)
    historyDF = historyDF.T

    now = datetime.now(timezone('EST'))

    while now.time() < time(8,30):
        now = datetime.now(timezone('EST'))
        symbolNum=0

        for symbol in stockSummaryDF['Symbol']:
            symbolNum = symbolNum +1
            try:
                stock = yf.Ticker(symbol)
                currentPrice = stock.fast_info['lastPrice']
            except:
                continue
            historyDF[symbol] = historyDF[symbol].shift(-1)
            historyDF[symbol][historyDF.shape[0]] = currentPrice
            
    
    stockSummaryDF['Buy Price'] = None
    stockSummaryDF['Buy Time'] = None
    stockSummaryDF['Sell Price'] = None
    stockSummaryDF['Sell Time'] = None
    stockSummaryDF['% Change'] = None


    while  now.time() <= time(15,45): #Run until 15min before market close
        
        #stop if all stocks sold
        if not stockSummaryDF['Sell Price'].isnull().any():
            break
            
        now = datetime.now(timezone('EST'))
        startMin = datetime.now().minute
        symbolNum=0
        
        for symbol in stockSummaryDF['Symbol']:
            
            symbolNum += 1
            
            try:
                stock = yf.Ticker(symbol)
                currentPrice = stock.fast_info['lastPrice']
            except:
                continue

            historyDF[symbol] = historyDF[symbol].shift(-1)
            historyDF[symbol][historyDF.shape[0]] = currentPrice
            
            try:
                #Get RSI and EMA
                delta = historyDF[symbol].diff()
                # Calculate gains and losses
                gains = delta.where(delta > 0, 0)
                losses = -delta.where(delta < 0, 0)
                avg_gain = gains.rolling(window=20, min_periods=1).mean()
                avg_loss = losses.rolling(window=20, min_periods=1).mean()
                RS = avg_gain / avg_loss
            except:
                continue
            
            RSI = 100 - (100 / (1 + RS.loc[historyDF.shape[0]]))
            EMA9 = historyDF[symbol].ewm(span=9, adjust=False).mean().loc[historyDF.shape[0]]
            EMA21 = historyDF[symbol].ewm(span=21, adjust=False).mean().loc[historyDF.shape[0]]
            EMA55 = historyDF[symbol].ewm(span=55, adjust=False).mean().loc[historyDF.shape[0]]

            SMA5 = historyDF[symbol].rolling(window=5).mean().loc[historyDF.shape[0]]
            SMA15 = historyDF[symbol].rolling(window=15).mean().loc[historyDF.shape[0]]
            SMA21 = historyDF[symbol].rolling(window=21).mean().loc[historyDF.shape[0]]

            #Bollinger Bands
            Rolling_Mean = historyDF[symbol].rolling(window=5).mean()
            Bollinger_Upper = Rolling_Mean + (historyDF[symbol].rolling(window=5).std() * 1.5)
            Bollinger_Lower = Rolling_Mean - (historyDF[symbol].rolling(window=5).std() * 1.5)
            Band_Width = Bollinger_Upper - Bollinger_Lower
            Avg_Band_Width = Band_Width.rolling(window=5).mean()
            percentB = ((Rolling_Mean[historyDF.shape[0]] - Bollinger_Lower[historyDF.shape[0]]) /
                        (Bollinger_Upper[historyDF.shape[0]] - Bollinger_Lower[historyDF.shape[0]]))

            BuyConditions = {
                    'EMA9': (EMA55, EMA9, 'less_than'),
                    'EMA21': (EMA55, EMA21, 'less_than'),
                    'SMA5': (SMA21, SMA5, 'less_than'),
                    'SMA15': (SMA21, SMA15, 'less_than'),
                    'RSI': (RSI, RSI_UNDERSOLD, 'less_than'),
                    'Rel_Volume': (stock.basic_info['lastVolume']/stock.basic_info['tenDayAverageVolume'], REL_VOL_UPPER, 'greater_than'),
                    'Bollinger_Breakout': (currentPrice, Bollinger_Lower[historyDF.shape[0]], 'less_than'),
                    'Bollinger_Squeeze': (Band_Width[historyDF.shape[0]], Avg_Band_Width[historyDF.shape[0]], 'less_than'),
                    'Percent_B': (percentB, PERCENT_B_Lower, 'less_than'),
                    'Time': (now.time(), time(11,0), 'less_than')
                }

            SellConditions = {
                    'EMA9': (EMA55, EMA9, 'greater_than'),
                    'EMA21': (EMA55, EMA21, 'greater_than'),
                    'SMA5': (SMA21, SMA5, 'greater_than'),
                    'SMA15': (SMA21, SMA15, 'greater_than'),
                    'RSI': (RSI, RSI_OVERSOLD, 'greater_than'),
                    'Rel_Volume': (stock.basic_info['lastVolume']/stock.basic_info['tenDayAverageVolume'], REL_VOL_LOWER, 'less_than'),
                    'Bollinger_Breakout': (currentPrice, Bollinger_Upper[historyDF.shape[0]], 'greater_than'),
                    'Bollinger_Squeeze': (Band_Width[historyDF.shape[0]], Avg_Band_Width[historyDF.shape[0]], 'greater_than'),
                    'Percent_B': (percentB, PERCENT_B_UPPER, 'greater_than'),
                    'Increase1': (currentPrice/float(stockSummaryDF[stockSummaryDF['Symbol'] == symbol]['Buy Price']), 1 + INCREASE_LOW, 'greater_than'),
                    'Increase2': (currentPrice/float(stockSummaryDF[stockSummaryDF['Symbol'] == symbol]['Buy Price']), 1 + INCREASE_HIGH, 'greater_than')
                }


            buySignal = Counter([check_condition(*cond) for cond in BuyConditions.values()])[True]/len(BuyConditions) >= 0.6
            sellSignal = Counter([check_condition(*cond) for cond in SellConditions.values()])[True]/len(SellConditions) >= 0.5
        
            #Buy stock if good to buy
            if stockSummaryDF.loc[symbolNum-1, 'Buy Price'] == None and now.time():
                if buySignal == True and now.time() <= LAST_BUY_TIME: 
                    
                    stockSummaryDF.loc[symbolNum-1, 'Buy Price'] = currentPrice
                    stockSummaryDF.loc[symbolNum-1, 'Buy Time'] = now.time()

                    message = str(symbol + " bought at " +  str(datetime.now().strftime('%H:%M:%S')) +
                           "\n Buy Price: " + str(float(stockSummaryDF[stockSummaryDF['Symbol'] == symbol]['Buy Price'])))
                     
                    send_telegram_message(message=message)

            #Check if stock is bought or sold 
            if stockSummaryDF.loc[symbolNum-1, 'Buy Price'] == None:
                continue
            if stockSummaryDF.loc[symbolNum-1, 'Sell Price'] != None:
                continue
            
            buyPrice = stockSummaryDF.loc[symbolNum-1, 'Buy Price']

            #Sell stock if time is good
            if sellSignal == True:
                sellPrice = currentPrice
                Change = ((sellPrice - buyPrice)/buyPrice)*100
                 
                stockSummaryDF.loc[symbolNum-1, 'Sell Price'] = sellPrice
                stockSummaryDF.loc[symbolNum-1, 'Sell Time'] = now.time()
                stockSummaryDF.loc[symbolNum-1, '% Change'] = Change
                 
                message = str(symbol + " sold at " +  str(datetime.now().strftime('%H:%M:%S')) +
                       "\n Buy Price: " + str(float(stockSummaryDF[stockSummaryDF['Symbol'] == symbol]['Buy Price'])) +
                       "\n Sell Price: "+ str(sellPrice) +
                       "\n % Increase: " + str(Change))
                 
                send_telegram_message(message=message)

            #Stop Loss
            elif (currentPrice < buyPrice*STOPLOSS):
                sellPrice = currentPrice
                buyPrice = stockSummaryDF.loc[symbolNum-1, 'Buy Price']
                Change = ((sellPrice - buyPrice)/buyPrice)*100
                
                stockSummaryDF.loc[symbolNum-1, 'Sell Price'] = sellPrice
                stockSummaryDF.loc[symbolNum-1, 'Sell Time'] = now.time()
                stockSummaryDF.loc[symbolNum-1, '% Change'] = Change
                
                message = str(symbol + " sold at " +  str(datetime.now().strftime('%H:%M:%S')) +
                      "\n Buy Price: " + str(float(stockSummaryDF[stockSummaryDF['Symbol'] == symbol]['Buy Price'])) +
                      "\n Sell Price: "+ str(sellPrice) +
                      "\n % Increase: " + str(Change))
                                
                send_telegram_message(message=message)
                
        
        #wait for stock to update
        endMin = datetime.now().minute
        while startMin == endMin:
            endMin = datetime.now().minute
        
    
    #Sell before market closes            
    symbolNum = 0
    for symbol in stockSummaryDF['Symbol']:
        
        symbolNum += 1
        if stockSummaryDF.loc[symbolNum-1, 'Buy Price'] == None:
            continue
        try:
            stock = yf.Ticker(symbol)
            currentPrice = stock.fast_info['lastPrice']
        except:
            continue

        if stockSummaryDF.loc[symbolNum-1, 'Sell Price'] == None:
            
            sellPrice = stock.fast_info['lastPrice']
            buyPrice = stockSummaryDF.loc[symbolNum-1, 'Buy Price']
            Change = ((sellPrice - buyPrice)/buyPrice)*100
            
            stockSummaryDF.loc[symbolNum-1, 'Sell Price'] = sellPrice
            stockSummaryDF.loc[symbolNum-1, 'Sell Time'] = now.time()
            stockSummaryDF.loc[symbolNum-1, '% Change'] = Change
                
            message = str(symbol + " did not sell before close" +
                      "\n Buy Price: " + str(float(stockSummaryDF[stockSummaryDF['Symbol'] == symbol]['Buy Price'])) +
                      "\n Sell Price: "+ str(sellPrice) +
                      "\n % Increase: " + str(Change))
            
            send_telegram_message(message=message)

            
    stockSummaryDF.dropna(inplace=True)        
    stockSummaryDF.reset_index(drop=True, inplace=True)


    #display(stockSummaryDF)
    message = str('Average %Change in Your Trades Today: \n' + str(round(statistics.mean(stockSummaryDF['% Change']),3)) + '%')
    send_telegram_message(message=message)
    
    return stockSummaryDF