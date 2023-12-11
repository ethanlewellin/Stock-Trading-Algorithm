# -*- coding: utf-8 -*-
"""
Telegram Setup

@author: ethan
"""

from Variables import telegram_url, myuserid
import requests

def send_telegram_message(message: str):
    
    response = requests.post(
        url= telegram_url,
        data={'chat_id': myuserid, 'text': message}
    ).json()
    
    return
    
