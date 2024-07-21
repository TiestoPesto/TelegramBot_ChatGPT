import asyncio
import uuid
from openai import OpenAI
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ContentType
import speech_recognition as sr
import logging
from dotenv import load_dotenv, find_dotenv
import os
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton


load_dotenv(find_dotenv())

language = 'ru_RU'
API_TOKEN = os.getenv('TG_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

# Установка ключа API OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_TOKEN'))

# Создание объекта бота
bot = Bot(token=os.getenv('TG_BOT_TOKEN'))
dp = Dispatcher(bot)
r = sr.Recognizer()

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# установка хедеров
headers = {
	'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
}

# Создаем папку, если ее нет
os.makedirs('../voice', exist_ok=True)
os.makedirs('../ready', exist_ok=True)


# Обработчик старта бота и приветствия
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
	try:
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
			welcome_text = (
				f"Привет, {message.from_user.first_name}! Я бот на базе ChatGPT, готовый помочь вам. Просто отправьте мне ваш вопрос и я постараюсь вам ответить."
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
				"Для безлимитного использования бота ChatGPT, подпишитесь на наш юмористический журнал: " + CHANNEL_USERNAME)
	except Exception as e:
		print(f"Ошибка старта бота: {e}")
		await message.answer("Произошла ошибка. Попробуйте еще раз позже.")


@dp.message_handler(commands=["help"])
async def send_start(message: types.Message):
	text = f"""Чтобы начать взаимодействие с ChatGPT без ограничения, подпишитесь на наш канал  {CHANNEL_USERNAME} и просто отправьте сообщение и бот ответит вам.

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
	await asyncio.sleep(2)
	await last_msg.edit_text(text)


# Обработчик голосового сообщения
async def recognise(filename):
	with sr.AudioFile(filename) as source:
		audio_text = r.listen(source)
		try:
			text = r.recognize_google(audio_text, language=language)
			print('Перевод аудио в текст ...')
			print(text)
			return text
		except Exception as e:
			print(f'Извините..у нас ошибка: {e}')
			return "Извините, скажите еще раз"


@dp.message_handler(content_types=ContentType.VOICE)
async def voice_processing(message: types.Message):
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
	
	await bot.send_chat_action(message.chat.id, "typing")
	last_msg = await message.answer(
		f"<code>Сообщение принято:</code>\n\n{text}",
		parse_mode="HTML",
		reply_markup=InlineKeyboardMarkup(
			inline_keyboard=[
				[
					InlineKeyboardButton(
						text="Отправить",
						callback_data=f"send_text:{text}"
					)
				]
			]
		)
	)
	
	await asyncio.sleep(1)
	
	await last_msg.edit_text(text)
	
	os.remove(file_name_full)
	os.remove(file_name_full_converted)


# Обработчик всех сообщений
@dp.message_handler()
async def handle_messages(message: types.Message):
	try:
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
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
		else:
			# Если пользователь не подписан, предлагаем подписаться
			await message.answer("Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
	except Exception as e:
		# Логируем ошибку
		logging.error(f"An error occurred: {e}")
		
		# При необходимости, уведомляем пользователя о проблеме
		await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")


# Обработчик callback-кнопки
@dp.callback_query_handler(lambda c: c.data.startswith('send_text:'))
async def process_callback_button(callback_query: types.CallbackQuery):
	_, text = callback_query.data.split(':')
	await bot.answer_callback_query(callback_query.id)
	await bot.send_message(callback_query.from_user.id, f"Вы выбрали отправку текста:\n{text}")

if __name__ == '__main__':
	# Включение long polling
	executor.start_polling(dp, skip_updates=True)
