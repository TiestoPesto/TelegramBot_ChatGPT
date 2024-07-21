"""Для экономии средств в качестве аудио модели распознавания используется библиотека Python
Добавлено сохранение контекста
"""
import asyncio
from openai import AsyncOpenAI
from aiogram import Bot, types, Dispatcher, executor
import logging
from dotenv import load_dotenv, find_dotenv
import os
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton
import speech_recognition as sr
import uuid
import sqlite3

load_dotenv(find_dotenv())
language = 'ru_RU'

API_TOKEN = os.getenv('TG_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
YOUR_CHANNEL_OWNER_ID = os.getenv('YOUR_CHANNEL_OWNER_ID')

# Установка ключа API OpenAI
client = AsyncOpenAI(
	api_key=os.environ.get("OPENAI_TOKEN"),
)

# Создание объекта бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создания объекта обработки голоса
recognizer = sr.Recognizer()

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Создаем папку, если ее нет
os.makedirs('./voice', exist_ok=True)
os.makedirs('./ready', exist_ok=True)

# Максимальное количество хранимых сообщений от пользователя
MAX_MESSAGES_PER_USER = 3

# Словарь для отслеживания контекста разговоров с пользователями
user_contexts = {}

# Создание базы данных SQLite и таблицы для хранения информации о пользователях
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        registration_date TEXT
    )
''')
conn.commit()


# Обработка запроса к GPT
async def send_to_openai(messages):
	try:
		response = await client.chat.completions.create(
			messages=messages,
			model="gpt-3.5-turbo",
		)
		
		logging.info(f"OpenAI API ответ:  {response}")
		return response.choices[0].message.content
	except Exception as e:
		logging.error(f"OpenAI API ошибка:, {e}")
		return "Извините, произошла ошибка. Мы работаем над решением проблемы. Пришлите Ваше сообщение еще раз"


# Обработчик старта бота и приветствия
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
	try:
		try:
			# Запись информации о пользователе в базу данных
			user_id = message.from_user.id
			username = message.from_user.username
			registration_date = message.date
			# Проверяем, есть ли уже пользователь с таким user_id в базе данных
			cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
			data = cursor.fetchone()
			
			# Если пользователя нет в базе данных, добавляем его
			if not data:
				cursor.execute('INSERT INTO users (id, username, registration_date) VALUES (?, ?, ?)',
				               (user_id, username, registration_date))
				conn.commit()
				conn.close()
		except Exception as e:
			logging.error(f"Ошибка БД бота 90 стр: {e}")
			
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
			welcome_text = (
				f"Привет, {message.from_user.first_name}! Я бот Govorunio на базе ChatGPT, готовый помочь вам. Просто отправьте мне ваш вопрос и я постараюсь вам ответить."
			)
			# await message.answer(welcome_text)
			await bot.send_chat_action(message.chat.id, "typing")
			last_msg = await message.answer(
				"<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
			)
			await asyncio.sleep(2)
			await last_msg.edit_text(welcome_text)
		else:
			# Если пользователь не подписан, предлагаем подписаться
			await message.answer(
				"Для безлимитного использования ботом ChatGPT, подпишитесь на наш юмористический журнал: " + CHANNEL_USERNAME)
	
	except Exception as e:
		logging.error(f"Ошибка старта бота: {e}")
		await message.answer("Произошла ошибка. Попробуйте еще раз позже.")


@dp.message_handler(commands=["help"])
async def send_start(message: types.Message):
	text = f"""Чтобы начать взаимодействие с ChatGPT без ограничения, подпишитесь на наш канал  {CHANNEL_USERNAME} и просто отправьте сообщение боту и он ответит вам.

Вы можете задавать ему любые вопросы, он обычно отвечает на них адекватно и быстро.

Также вы можете использовать бота для выполнения различных задач, например, он может вывести расписание фильмов, погоду, новости, анекдоты и многое другое.

Кроме того, ChatGPT может быть использован для проведения небольших игр и конкурсов с пользователями.

Возможности бота очень широки, и вы можете экспериментировать и сами пробовать всевозможные примеры работы с ним. Не стесняйтесь обращаться к ChatGPT за помощью, он всегда готов вам помочь!

👋Если вопрос касается сотрудничества, обратитесь к - @Nick_Sam
"""
	await bot.send_chat_action(message.chat.id, "typing")
	last_msg = await message.answer(
		"<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
	)
	await asyncio.sleep(2)
	await last_msg.edit_text(text)


@dp.message_handler(commands=['users_bot'])
async def show_users(message: types.Message):
	"""
	Обработчик команды /users_bot.
	Выводит список всех пользователей из базы данных.
	"""
	# Проверка на ID владельца канала
	if message.from_user.id != YOUR_CHANNEL_OWNER_ID:
		await message.answer("Извините, у вас нет доступа к этой команде.")
		return
	
	cursor.execute('SELECT * FROM users')
	users = cursor.fetchall()
	if users:
		all_users = len(users)
		response = f"Список пользователей:\nВсего пользователей:     {all_users}\n"
		
		numbers = 0
		for user in users:
			numbers += 1
			response += f"\n№ {numbers} \nID:     {user[0]},\nUsername:      @{user[1]},\n" \
			            f"Registration Date:        {user[2]}\n"
	else:
		response = "Список пользователей пуст."
	await message.answer(response)


# Функция для очистки контекста пользователя
async def clear_user_context(user_id):
	await asyncio.sleep(200)  # Ожидаем 3,3 минуты
	if user_id in user_contexts:
		del user_contexts[user_id]
		logging.info(f"Прошло 3 минуты. Контекст пользователя {user_id} очищен.")


# Обработчик голосовых сообщений
async def recognise(filename):
	with sr.AudioFile(filename) as source:
		audio_text = recognizer.listen(source)
		try:
			text = recognizer.recognize_google(audio_text, language=language)
			logging.error(f'Перевод аудио в текст: {text}')
			
			return text
		except Exception as e:
			logging.error(f'Извините..у нас ошибка: {e}')
			return "Извините, Вас плохо слышно, скажите пожалуйста еще раз и отчетливо"


@dp.message_handler(content_types=ContentType.VOICE)
async def handle_voice(message: types.Message):
	try:
		
		try:
			# Запись информации о пользователе в базу данных
			user_id = message.from_user.id
			username = message.from_user.username
			registration_date = message.date
			# Проверяем, есть ли уже пользователь с таким user_id в базе данных
			cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
			data = cursor.fetchone()
			
			# Если пользователя нет в базе данных, добавляем его
			if not data:
				cursor.execute('INSERT INTO users (id, username, registration_date) VALUES (?, ?, ?)',
				               (user_id, username, registration_date))
				conn.commit()
				conn.close()
		except Exception as e:
			logging.error(f"Ошибка БД бота 90 стр: {e}")
		
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
			try:
				await bot.send_chat_action(message.chat.id, "typing")
				last_msg = await message.answer(
					"<code>Сообщение принято. Занимаемся распознаванием...</code>", parse_mode="HTML"
				)
				filename = str(uuid.uuid4())
				file_name_full = "./voice/" + filename + ".ogg"
				file_name_full_converted = "./ready/" + filename + ".wav"
				file_info = await bot.get_file(message.voice.file_id)
				downloaded_file = await bot.download_file(file_info.file_path)
				
				# Используем метод read(), чтобы получить байты
				downloaded_bytes = downloaded_file.read()
				
				with open(file_name_full, 'wb') as new_file:
					new_file.write(downloaded_bytes)
				
				os.system("ffmpeg -i " + file_name_full + "  " + file_name_full_converted)
				text = await recognise(file_name_full_converted)
				
				# await last_msg.edit_text(text)
				
				# Создаем клавиатуру
				keyboard = InlineKeyboardMarkup()
				# Добавляем кнопку "Отправить"
				keyboard.add(InlineKeyboardButton("Отправить Говоруше?", callback_data="send_message"))
				
				# Отправляем сообщение с клавиатурой
				# await message.answer(text=text, reply_markup=keyboard)
				await last_msg.edit_text(text=text, reply_markup=keyboard)
				
				os.remove(file_name_full)
				os.remove(file_name_full_converted)
			
			except Exception as e:
				logging.error(f"Ошибка в голосовом сообщении: {e}")
				
				# При необходимости, уведомляем пользователя о проблеме
				await message.answer(
					"Извините, произошла ошибка. Мы работаем над решением проблемы. Отправьте ваше сообщение еще раз.")
		
		else:
			# Если пользователь не подписан, предлагаем подписаться
			await message.answer("Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
	
	except Exception as e:
		# Логируем ошибку
		logging.error(f"Ошибка голосового сообщения: {e}")
		# При необходимости, уведомляем пользователя о проблеме
		await message.answer(
			"Извините, произошла ошибка на сервере. Мы работаем над решением проблемы."
			" Попробуйте повторить ваше сообщение чуть позже.")


# Обработчик всех сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_messages(message: types.Message):
	try:
		
		try:
			# Запись информации о пользователе в базу данных
			user_id = message.from_user.id
			username = message.from_user.username
			registration_date = message.date
			# Проверяем, есть ли уже пользователь с таким user_id в базе данных
			cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
			data = cursor.fetchone()
			
			# Если пользователя нет в базе данных, добавляем его
			if not data:
				cursor.execute('INSERT INTO users (id, username, registration_date) VALUES (?, ?, ?)',
				               (user_id, username, registration_date))
				conn.commit()
				conn.close()
		except Exception as e:
			logging.error(f"Ошибка БД бота 90 стр: {e}")
		
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
			# Выводим в консоль сообщение от пользователя
			logging.info(f"Сообщение от  {message.from_user.username}, {message.text}")
			
			# Отправляем промежуточное сообщение ожидания
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
			
			# Запускаем таймер для очистки контекста пользователя через 2 минуты
			asyncio.create_task(clear_user_context(user_id))
		
		else:
			# Если пользователь не подписан, предлагаем подписаться
			await message.answer("Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
	
	except Exception as e:
		# Логируем ошибку
		logging.error(f"Ошибка в блоке сообщений: {e}")
		# При необходимости, уведомляем пользователя о проблеме
		await message.answer(
			"Извините, произошла ошибка сервера. Мы работаем над решением проблемы. "
			"Отправьте ваше сообщение еще раз через пару минут.")


# Добавим обработчик для кнопки "Отправить"
@dp.callback_query_handler(lambda callback_query: callback_query.data == "send_message")
async def send_message(callback_query: types.CallbackQuery):
	try:
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, callback_query.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
			# Выводим в консоль сообщение от пользователя
			logging.info(f"Сообщение от  {callback_query.from_user.username}, {callback_query.message.text}")
			
			# Отправляем промежуточное сообщение ожидания
			await bot.send_chat_action(callback_query.message.chat.id, "typing")
			last_msg = await callback_query.message.answer(
				"Сообщение принято. Ждем ответа от Говоруши...",
			)
			
			await callback_query.answer()
			
			# Проверка, есть ли контекст для данного пользователя
			user_id = callback_query.from_user.id
			if user_id not in user_contexts:
				user_contexts[user_id] = []
			
			# Добавление сообщения от пользователя в контекст
			user_contexts[user_id].append({'role': 'user', 'content': callback_query.message.text})
			
			# Ограничение числа хранимых сообщений
			if len(user_contexts[user_id]) > MAX_MESSAGES_PER_USER:
				user_contexts[user_id].pop(0)  # Удаление старого сообщения из начала списка
			
			# Отправка контекста в OpenAI API
			text = await send_to_openai(user_contexts[user_id])
			
			# Добавление сообщения от ассистента в контекст
			user_contexts[user_id].append({'role': 'system', 'content': text})
			
			await last_msg.edit_text(text)
		
		else:
			# Если пользователь не подписан, предлагаем подписаться
			await bot.send_message(callback_query.message.chat.id,
			                       "Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
	
	except Exception as e:
		logging.error(f"An error occurred: {e}")
		# При необходимости, уведомляем пользователя о проблеме
		await bot.send_message(callback_query.message.chat.id,
		                       "Извините, произошла ошибка. Мы работаем над решением проблемы.")


if __name__ == '__main__':
	# Включение long polling
	executor.start_polling(dp, skip_updates=True)
