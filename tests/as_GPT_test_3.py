import asyncio
import logging
import os
from dotenv import load_dotenv, find_dotenv
from aiogram import Bot, types, Dispatcher, executor
from openai import AsyncOpenAI

load_dotenv(find_dotenv())
language = 'ru_RU'

API_TOKEN = os.getenv('TG_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

# Установка ключа API OpenAI
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_TOKEN"))

# Создание объекта бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Максимальное количество хранимых сообщений от пользователя
MAX_MESSAGES_PER_USER = 5

# Словарь для отслеживания контекста разговоров с пользователями
user_contexts = {}


async def send_to_openai(messages):
	try:
		response = await client.chat.completions.create(
			messages=messages,
			model="gpt-3.5-turbo",
		)
		
		logging.info("OpenAI API Response: %s", response)
		return response.choices[0].message.content
	except Exception as e:
		logging.error("OpenAI API Error: %s", e)
		return "Извините, произошла ошибка. Мы работаем над решением проблемы. Пришлите Ваше сообщение еще раз"


@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_messages(message: types.Message):
	try:
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		if chat_member.is_chat_member():
			logging.info("Сообщение от %s: %s", message.from_user.username, message.text)
			await bot.send_chat_action(message.chat.id, "typing")
			last_msg = await message.answer("<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML")
			
			# Проверка, есть ли контекст для данного пользователя
			user_id = message.from_user.id
			if user_id not in user_contexts:
				user_contexts[user_id] = []
			
			# Добавление сообщения от пользователя в контекст
			user_contexts[user_id].append({'role': 'user', 'content': message.text})
			
			# Ограничение числа хранимых сообщений
			if len(user_contexts[user_id]) > MAX_MESSAGES_PER_USER:
				user_contexts[user_id].pop(0)  # Удаление старого сообщения из начала списка
			
			# Отправка контекста в OpenAI API
			text = await send_to_openai(user_contexts[user_id])
			
			# Добавление сообщения от ассистента в контекст
			user_contexts[user_id].append({'role': 'system', 'content': text})
			
			await last_msg.edit_text(text)
		
		else:
			await message.answer("Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
	except Exception as e:
		logging.error("An error occurred: %s", e)
		await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")


if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)

