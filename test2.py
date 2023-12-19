from aiohttp import ClientSession, TCPConnector
from openai import OpenAI
from aiogram import Bot, types, Dispatcher, executor
import config
import logging
import time
import os
from dotenv import load_dotenv

# Установка ключа API OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_TOKEN'))

# Создание объекта бота
bot = Bot(token=os.getenv('TG_BOT_TOKEN'))
dp = Dispatcher(bot)

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# установка хедеров
headers = {
	'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
}
ip = os.getenv('ip')
port = os.getenv('port')
# Установка прокси
proxy = {
	'https': f'http://{ip}:{port}'
}
connector = TCPConnector.from_url(proxy)


# Обработчик старта бота и приветствия
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
	welcome_text = (
		f"Привет, {message.from_user.first_name}! Я бот на базе ChatGPT, готовый помочь вам. Просто отправьте мне ваш вопрос и я постараюсь вам ответить."
	)
	# await message.answer(welcome_text)
	await bot.send_chat_action(message.chat.id, "typing")
	last_msg = await message.answer(
		"<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
	)
	time.sleep(2)
	await last_msg.edit_text(welcome_text)


@dp.message_handler(commands=["help"])
async def send_start(message: types.Message):
	text = """Чтобы начать взаимодействие с ChatGPT, просто отправьте сообщение и бот ответит вам.

Вы можете задавать ему любые вопросы, он обычно отвечает на них адекватно и быстро.

Также вы можете использовать бота для выполнения различных задач, например, он может вывести расписание фильмов, погоду, новости, анекдоты и многое другое.

Кроме того, ChatGPT может быть использован для проведения небольших игр и конкурсов с пользователями.

Возможности бота очень широки, и вы можете экспериментировать и сами пробовать всевозможные примеры работы с ним. Не стесняйтесь обращаться к ChatGPT за помощью, он всегда готов вам помочь!

👋Если вопрос касается сотрудничества, обратитесь к - @gpt_dim
"""
	await bot.send_chat_action(message.chat.id, "typing")
	last_msg = await message.answer(
		"<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
	)
	time.sleep(3)
	await last_msg.edit_text(text)


# Обработчик всех сообщений
@dp.message_handler()
async def handle_messages(message: types.Message):
	try:
		# Выводим в консоль сообщение от пользователя
		print(f"Сообщение от {message.from_user.username}: {message.text}")
		
		# Отправляем промежуточное сообщение ожидания
		await bot.send_chat_action(message.chat.id, "typing")
		last_msg = await message.answer(
			"<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
		)
		
		chat_completion = client.chat.completions.create(
			messages=[
				{
					"role": "user",
					"content": message.text,
				}
			],
			model="gpt-3.5-turbo",
		)
		
		print(chat_completion.choices[0].message.content)
		await last_msg.edit_text(chat_completion.choices[0].message.content)
	# await message.answer(chat_completion.choices[0].message.content)
	
	except Exception as e:
		# Логируем ошибку
		logging.error(f"An error occurred: {e}")
		
		# При необходимости, уведомляем пользователя о проблеме
		await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")


if __name__ == '__main__':
	# Включение long polling
	executor.start_polling(dp, skip_updates=True)
