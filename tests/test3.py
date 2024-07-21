import asyncio
from openai import OpenAI
from aiogram import Bot, types, Dispatcher, executor
import config
import logging
import time
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

API_TOKEN = os.getenv('TG_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

# Установка ключа API OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_TOKEN'))

def request_chat():
	chat_completion = client.chat.completions.create(
		messages=[
			{
				"role": "user",
				"content": 'Привет как дела?',
			}
		],
		model="gpt-3.5-turbo",
	)
	
	print(chat_completion.choices[0].message.content)
	
if __name__ == '__main__':
	request_chat()