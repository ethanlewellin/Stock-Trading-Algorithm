# -*- coding: utf-8 -*-
"""
Stock Trading Algorithm Global Variables/Parameters

@author: ethan
"""
#Imports
from datetime import datetime, date, timedelta, time

#datetime
today = date.today()
yesterday = datetime.now() - timedelta(1)

#Telegram
token = "6881038859:AAFsRIVhhkzdRNhNYH77QFNId1qKsYmmMr8"
method = 'sendMessage'
myuserid = 6685760530
telegram_url = 'https://api.telegram.org/bot{0}/{1}'.format(token, method)

#Stock Screener
SCREEN_MAX_PRICE = 5 #M
SCREEN_VOL_RATIO = 5
SCREEN_RSI_MAX = 60

#Model
N_ESTIMATORS = 10000 #n_estimators for random forest
# class_weight gives different penalties for false positives and false
# negitives when training random forests
# Default below give a 10x penalty to classifying a True (good stock to buy)
# when actual is false
class_weight_TRUE = 10 
class_weight_FALSE = 1
#False Positive allowance in training to determine if a stock is good to buy
#serves as a confidence measure
#1-allows all stocks that were classified as buy
FP_ALLOWANCE = 0.2 

#Buy/Sell Routine
RSI_UNDERSOLD = 30 #What RSI to consider a stock undersold
REL_VOL_UPPER = 1.2 #Ratio between current volume and 10 day avg volume to determine buy call
PERCENT_B_Lower = 0.3 #%B to consider a stock undersold

RSI_OVERSOLD = 70 #What RSI to consider a stock oversold
REL_VOL_LOWER = 9 #Ratio between current volume and 10 day avg volume to determine sell call
PERCENT_B_UPPER = 0.7 #%B to consider a stock oversold
INCREASE_LOW = 0.05 #Low goal to sell
INCREASE_HIGH = 0.1 #High goal to sell

LAST_BUY_TIME = time(12,0) #last time to be able to buy

STOPLOSS = 0.95 #Stop Loss to sell at a loss

def check_condition(value, threshold, condition_type): #Check buy/sell metrics
    if condition_type == 'greater_than':
        return value > threshold
    elif condition_type == 'less_than':
        return value < threshold
    else:
        return False
    
