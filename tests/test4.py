import asyncio
from aiogram import Bot, types, Dispatcher, executor
import logging
import os
from aiogram.types import ContentType
import speech_recognition as sr
import uuid
from dotenv import load_dotenv, find_dotenv


# Установка уровня логирования
logging.basicConfig(level=logging.INFO)
load_dotenv(find_dotenv())
language = 'ru_RU'

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Создания объекта обработки голоса
recognizer = sr.Recognizer()

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Создаем папку, если ее нет
os.makedirs('./voice', exist_ok=True)
os.makedirs('./ready', exist_ok=True)




# Обработчик старта бота и приветствия
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
	try:
		# Получаем информацию о пользователе в канале
		chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
		# Проверяем, является ли пользователь подписчиком канала
		if chat_member.is_chat_member():
			welcome_text = (
				f"Привет, {message.from_user.first_name}! Я бот Govorunio Rec готов распознать твои сообщения и написать текст"
			)
			# await message.answer(welcome_text)
			await bot.send_chat_action(message.chat.id, "typing")
			last_msg = await message.answer(
				"<code>Сообщение принято. Распознаю...</code>", parse_mode="HTML"
			)
			await asyncio.sleep(2)
			await last_msg.edit_text(welcome_text)
		else:
			# Если пользователь не подписан, предлагаем подписаться
			await message.answer(
				"Для безлимитного использования ботом Govorunio Rec, подпишитесь на наш юмористический журнал: " + CHANNEL_USERNAME)
	except Exception as e:
		logging.error(f"Ошибка старта бота: {e}")
		await message.answer("Произошла ошибка. Попробуйте еще раз позже.")


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
				
				await last_msg.edit_text(text)
				
				
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
			"Извините, произошла ошибка на сервере. Мы работаем над решением проблемы. Попробуйте повторить ваше сообщение чуть позже.")


# Запуск бота
if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)
