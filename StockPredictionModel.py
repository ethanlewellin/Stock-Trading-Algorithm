# -*- coding: utf-8 -*-
"""
Stock Prediction Model

@author: ethan
"""
from Variables import today, N_ESTIMATORS, class_weight_TRUE, class_weight_FALSE, FP_ALLOWANCE
import pandas as pd
import numpy as np
from datetime import date, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf
import warnings

pd.options.mode.chained_assignment = None
warnings.simplefilter("ignore")

def ema(values, period):
    values = np.array(values)
    return pd.ewm(values, span=period)[-1]

scalerX = MinMaxScaler(feature_range=(0,1))
scalerY = MinMaxScaler(feature_range=(0,1))
    
def Predict_Stocks(tickers):

    print('Predicting Stocks')
    
    end_date = today.strftime("%Y-%m-%d")
    d1 = date.today() - timedelta(days=360*5) #for last 5 years
    start_date = d1.strftime("%Y-%m-%d")

    stockData = yf.download(tickers = tickers[:],
                      start = start_date,
                      end = end_date,
                      progress=False)
    
    stockSummaryList = []
    
    #Model each stock
    for symbol in tickers:
        try:        
            try:
                stock = yf.Ticker(symbol)
                currentPrice = stock.fast_info['lastPrice']
                currentVol = stock.fast_info['lastVolume']
                if stock.fast_info['timezone'] != 'America/New_York': #Only Look at US stocks
                    continue
                if currentPrice < 0.005: #Skip really small stocks that give yfinance bad data reads
                    continue
            except:
                continue
        
            idvStock = stockData.loc[:, (slice(None), symbol)]
            idvStock = idvStock.dropna()
            
            #Get Close SMAs and EMAs
            idvStock['Close 5SMA'] = idvStock['Close'].rolling(window=5).mean().shift(1)
            idvStock['Close 10SMA'] = idvStock['Close'].rolling(window=10).mean().shift(1)
            idvStock['Close 20SMA'] = idvStock['Close'].rolling(window=20).mean().shift(1)
            idvStock['Close 9EMA'] = idvStock['Close'].ewm(span=9, adjust=False).mean().shift(1)
            idvStock['Close 12EMA'] = idvStock['Close'].ewm(span=12, adjust=False).mean().shift(1)
            idvStock['Close 26EMA'] = idvStock['Close'].ewm(span=26, adjust=False).mean().shift(1)
            
            #Get High SMAs and EMAs
            idvStock['High 5SMA'] = idvStock['High'].rolling(window=2).mean().shift(1)
            idvStock['High 10SMA'] = idvStock['High'].rolling(window=10).mean().shift(1)
            idvStock['High 20SMA'] = idvStock['High'].rolling(window=20).mean().shift(1)
            idvStock['High 9EMA'] = idvStock['High'].ewm(span=9, adjust=False).mean().shift(1)
            idvStock['High 12EMA'] = idvStock['High'].ewm(span=12, adjust=False).mean().shift(1)
            idvStock['High 26EMA'] = idvStock['High'].ewm(span=26, adjust=False).mean().shift(1)
            
            #Get 1 2 and 3 month Avg Volume
            idvStock['1m AVol'] = idvStock['Volume'].rolling(window=30).mean().shift(1)
            idvStock['2m AVol'] = idvStock['Volume'].rolling(window=60).mean().shift(1)
            idvStock['3m AVol'] = idvStock['Volume'].rolling(window=90).mean().shift(1)
            
            #Get RSIs
            delta = idvStock['Close'].diff()
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
        
            idvStock['10RS'] = gains.rolling(window=10, min_periods=1).mean().shift(1) / losses.rolling(window=10, min_periods=1).mean().shift(1)
            idvStock['20RS'] = gains.rolling(window=20, min_periods=1).mean().shift(1) / losses.rolling(window=20, min_periods=1).mean().shift(1)
            idvStock['30RS'] = gains.rolling(window=30, min_periods=1).mean().shift(1) / losses.rolling(window=30, min_periods=1).mean().shift(1)
        
            #Drop NAs and Reindex
            idvStock.replace([np.inf, -np.inf], np.nan, inplace=True)
            idvStock = idvStock.dropna()
            idvStock.reset_index(inplace=True)
        
            idvStock['day'] = idvStock['Date'].dt.day
            idvStock['month'] = idvStock['Date'].dt.month
            idvStock['year'] = idvStock['Date'].dt.year
            
            #Create Target Variable of >10% Increase
            idvStock['profitGoal'] = (
                ((idvStock['High']-idvStock['Open'])/idvStock['Open'] *100)>10)
            
            X_train =  scalerX.fit_transform(
                idvStock[['Open',
                          'Volume',
                          'day',
                          'month',
                          'year',
                          'Close 5SMA',
                          'Close 10SMA',
                          'Close 20SMA',
                          'Close 9EMA',
                          'Close 12EMA',
                          'Close 26EMA',
                          'High 5SMA',
                          'High 10SMA',
                          'High 20SMA',
                          'High 9EMA',
                          'High 12EMA',
                          'High 26EMA',
                          '10RS',
                          '20RS',
                          '30RS',
                          '1m AVol',
                          '2m AVol',
                          '3m AVol']])
            
            y_train = idvStock['profitGoal']
            
            todayData = np.array(
                [currentPrice,
                 currentVol,
                 today.day,
                 today.month,
                 today.year,
                 np.array(idvStock['Close'].rolling(window=5).mean()[-1:])[0][0],
                 np.array(idvStock['Close'].rolling(window=10).mean()[-1:])[0][0],
                 np.array(idvStock['Close'].rolling(window=20).mean()[-1:])[0][0],
                 np.array(idvStock['Close'].ewm(span=9, adjust=False).mean()[-1:])[0][0],
                 np.array(idvStock['Close'].ewm(span=12, adjust=False).mean()[-1:])[0][0],
                 np.array(idvStock['Close'].ewm(span=26, adjust=False).mean()[-1:])[0][0],
                 np.array(idvStock['High'].rolling(window=2).mean()[-1:])[0][0],
                 np.array(idvStock['High'].rolling(window=10).mean()[-1:])[0][0],
                 np.array(idvStock['High'].rolling(window=20).mean()[-1:])[0][0],
                 np.array(idvStock['High'].ewm(span=9, adjust=False).mean()[-1:])[0][0],
                 np.array(idvStock['High'].ewm(span=12, adjust=False).mean()[-1:])[0][0],
                 np.array(idvStock['High'].ewm(span=26, adjust=False).mean()[-1:])[0][0],
                 np.array(gains.rolling(window=10, min_periods=1).mean()[-1:] / losses.rolling(window=10, min_periods=1).mean()[-1:])[0][0],
                 np.array(gains.rolling(window=20, min_periods=1).mean()[-1:]/ losses.rolling(window=20, min_periods=1).mean()[-1:])[0][0],
                 np.array(gains.rolling(window=30, min_periods=1).mean()[-1:] / losses.rolling(window=30, min_periods=1).mean()[-1:])[0][0],
                 np.array(idvStock['Volume'].rolling(window=30).mean()[-1:])[0][0],
                 np.array(idvStock['Volume'].rolling(window=60).mean()[-1:])[0][0],
                 np.array(idvStock['Volume'].rolling(window=90).mean()[-1:])[0][0]
                 ])
            
            todayData = todayData.reshape(1,-1)
            todayData = scalerX.transform(todayData)
            
            clf = RandomForestClassifier(criterion='entropy',
                                         n_estimators = N_ESTIMATORS,
                                         bootstrap=True,
                                         warm_start=True,
                                         class_weight={True:class_weight_TRUE, False:class_weight_FALSE},
                                         oob_score=True
                                         )
            clf.fit(X_train, y_train)
            tainPredictions = clf.predict(X_train)
            tn, fp, fn, tp = confusion_matrix(y_train, tainPredictions, labels=[False,True], normalize='all').ravel()
            todayPred = clf.predict(todayData)
            
            
            if todayPred and fp < FP_ALLOWANCE:
                
                stockSummaryList.append(
                         [symbol,
                          stock.fast_info['lastPrice']])
        except:
            continue
    print('Done Predicting Stocks')
    return(pd.DataFrame(stockSummaryList, columns=['Symbol','Open Price']))
