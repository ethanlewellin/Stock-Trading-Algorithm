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
from Variables import today, SCREEN_MAX_PRICE, SCREEN_VOL_RATIO, SCREEN_RSI_MAX #If you have finviz pro you can incorporate these but I do not
import string    

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
    
    url = "https://finviz.com/screener.ashx?v=111&f=an_recom_buybetter,geo_usa,sh_price_u5,sh_relvol_o5,ta_rsi_nob60,targetprice_a10&o=-relativevolume"
    
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
        
    response = urllib.request.urlopen(req)
        
    html = response.read()
    soup = BeautifulSoup(html, parser='lxml', features='lxml')
        
    table = soup.find('table', {'class': "styled-table-new is-rounded is-tabular-nums w-full screener_table"})
        
    if table:
            # Iterate through the rows and cells to extract the data
            data = []
            headers = ['No.','Ticker','Company','Sector','Industry','Country','Market Cap','P/E','Price	Change','Volume']
        
            for row in table.find_all('tr'):
                columns = row.find_all('td')
                if columns:
                    # Extract and print the data from all columns
                    column_data = [column.get_text() for column in columns]
                    data.append(dict(zip(headers, column_data)))
        
    finvizDF = pd.concat([pd.Series(row) for row in data], axis=1).T
    # Close the HTTP response
    response.close()
                                
    finvizSymbols = list(finvizDF['Ticker'])
        
    print("Finished Screening Stocks")
    return list(set(finvizSymbols + yahooSymbols))