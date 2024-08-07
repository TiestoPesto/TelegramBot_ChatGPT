'''Тут используется аудио модель Чата GPT которая снимает плату
за распознавание аудио'''
import asyncio
from openai import AsyncOpenAI
from aiogram import Bot, types, Dispatcher, executor
import logging
from dotenv import load_dotenv, find_dotenv
import os
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton
import speech_recognition as sr
import uuid

load_dotenv(find_dotenv())
language = 'ru_RU'

API_TOKEN = os.getenv('TG_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

# Установка ключа API OpenAI
client = AsyncOpenAI(
	# This is the default and can be omitted
	api_key=os.environ.get("OPENAI_TOKEN"),
)

# Создание объекта бота
bot = Bot(token=os.getenv('TG_BOT_TOKEN'))
dp = Dispatcher(bot)

# Создания объекта обработки голоса
r = sr.Recognizer()

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Создаем папку для сохранения голосовых сообщений
os.makedirs('./voice', exist_ok=True)

# установка хедеров
headers = {
	'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
}


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


# Обработчик голосовых сообщений
@dp.message_handler(content_types=ContentType.VOICE)
async def handle_voice(message: types.Message):
	try:
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
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
			try:
				
				# Отправляем промежуточное сообщение ожидания
				await bot.send_chat_action(message.chat.id, "typing")
				last_msg = await message.answer(
					"<code>Сообщение принято. Занимаемся распознаванием...</code>", parse_mode="HTML"
				)
				
				# Отправляем запрос на распознавание голоса в OpenAI
				with open(file_name_full_converted, 'rb') as wav_file:
					
					response_data = await client.audio.transcriptions.create(
						model="whisper-1",
						file=wav_file,
						# response_format="text"
					)
				
				# Получаем транскрипт из ответа OpenAI
				# transcription_data = response_data.json()
				# transcript = transcription_data["data"]["text"]
				print(response_data.text)
				
				# Отправляем транскрипт в чат
				# await bot.send_message(message.chat.id, f"Текст: {response_data.text}")
				await last_msg.edit_text(f"Текст:  {response_data.text}")
			
			except Exception as e:
				logging.error(f"Ошибка в голосовом сообщении: {e}")
				
				# При необходимости, уведомляем пользователя о проблеме
				await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")
			
			finally:
				# Удаляем сохраненный файл
				os.remove(file_name_full)
				os.remove(file_name_full_converted)
		else:
			# Если пользователь не подписан, предлагаем подписаться
			await message.answer("Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
	except Exception as e:
		# Логируем ошибку
		logging.error(f"An error occurred: {e}")
		
		# При необходимости, уведомляем пользователя о проблеме
		await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")

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
			
			chat_completion = await client.chat.completions.create(
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


if __name__ == '__main__':
	# Включение long polling
	executor.start_polling(dp, skip_updates=True)
