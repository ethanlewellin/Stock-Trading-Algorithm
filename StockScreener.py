# -*- coding: utf-8 -*-
"""
Stock Algorithm Stock Screener

@author: ethan lewellin
"""

# Imports
import pandas as pd
import urllib.request
from datetime import date, timedelta
from urllib.request import Request
from bs4 import BeautifulSoup
import yfinance as yf
from Variables import today, SCREEN_MAX_PRICE, SCREEN_VOL_RATIO, SCREEN_RSI_MAX
import string    

alphabet = list(string.ascii_uppercase)

def Screen_Stocks():
    
    print("Screening Stocks")
    
    url = "https://finance.yahoo.com/u/yahoo-finance/watchlists/most-active-penny-stocks"
    
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    response = urllib.request.urlopen(req)
    
    html = response.read()
    soup = BeautifulSoup(html, parser='lxml', features='lxml')
    
    table = soup.find('table', {'class': 'cwl-symbols W(100%)'})
    
    
    if table:
        # Iterate through the rows and cells to extract the data
        data = []
        headers = ["Symbol", "Company Name", "Last Price", "Change", "% Change", "Market Time", "Volume", "Avg Vol (3 month)", "Market Cap"]
    
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if columns:
                # Extract and print the data from all columns
                column_data = [column.get_text() for column in columns]
                data.append(dict(zip(headers, column_data)))
    
    yahooPS = pd.concat([pd.Series(row) for row in data], axis=1).T
    # Close the HTTP response
    response.close()
                            
    #display(yahooPS)
    yahooPS = pd.DataFrame(yahooPS)
    yahooSymbols = list(yahooPS[yahooPS["Volume"] > SCREEN_VOL_RATIO* yahooPS["Avg Vol (3 month)"]]["Symbol"])
    
    tickers = []
    for letter in alphabet:
        url = 'https://stock-screener.org/stock-list.aspx?alpha=' + letter
        
        req = Request(
            url=url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        response = urllib.request.urlopen(req)
        
        
        html = response.read()
        soup = BeautifulSoup(html, parser='lxml', features='lxml')
        
        table = soup.find('table', {'class': 'styled'})
        
        if table:
            # Iterate through the rows and cells to extract the data
            data = []
            headers = ["Symbol","Chart","Open","High","Low","Close","Volume","% Change","Stock Predictions"]
        
            for row in table.find_all('tr'):
                columns = row.find_all('td')
                if columns:
                    # Extract and print the data from all columns
                    column_data = [column.get_text() for column in columns]
                    data.append(dict(zip(headers, column_data)))
                    
        df = pd.DataFrame(pd.concat([pd.Series(row) for row in data], axis=1).T)
        df['Symbol'] = [symbol.strip() for symbol in df['Symbol']]
        df['Volume'] = pd.to_numeric(df['Volume'])
        df['Open'] = pd.to_numeric(df['Open'])
        df = df[df['Symbol'].str.isalpha()] #get rid of error causing tickers
        df = df[df['Open'] < SCREEN_MAX_PRICE] #look at stocks below price point
        tickers = tickers + list(df['Symbol'][df['Open'] < SCREEN_MAX_PRICE])
        
        response.close()
    
    end_date = today.strftime("%Y-%m-%d")
    d1 = date.today() - timedelta(days=360*5) #for last 5 years
    start_date = d1.strftime("%Y-%m-%d")
    
    stockData = yf.download(tickers = tickers[:],
                      start = start_date,
                      end = end_date,
                      progress=False
                      )
    
    screenedStockSymbols = []
    for symbol in tickers:
        try:
            stock = yf.Ticker(symbol)
            idvStock = stockData.loc[:, (slice(None), symbol)]
            idvStock = idvStock.dropna()
            
            delta = idvStock['Close'].diff()
            # Calculate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            avg_gain = gains.rolling(window=20, min_periods=1).mean()
            avg_loss = losses.rolling(window=20, min_periods=1).mean()
            RS = avg_gain / avg_loss
            
            RSI = 100 - (100 / (1 + RS[-1:])) < SCREEN_RSI_MAX
            Vol_Ratio = stock.basic_info['lastVolume'] > SCREEN_VOL_RATIO*stock.basic_info['threeMonthAverageVolume']
            #Trend = stock.basic_info['fiftyDayAverage'] > stock.basic_info['twoHundredDayAverage']
            
            if (RSI[symbol][0] and Vol_Ratio and Trend):
                screenedStockSymbols.append(symbol)
        except:
            continue
        
    print("Finished Screening Stocks")
    return list(set(screenedStockSymbols + yahooSymbols))