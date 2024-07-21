import asyncio
import logging
import uuid
import os
import io
import aiogram
from aiogram import types
from aiogram import Bot, Dispatcher
from aiogram.types import ContentType
import speech_recognition as sr
from config import API_TOKEN
from aiogram import executor
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton

language = 'ru_RU'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
r = sr.Recognizer()

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Создаем папку, если ее нет
os.makedirs('./voice', exist_ok=True)
os.makedirs('./ready', exist_ok=True)


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
	
	
	
	# await message.answer(
	# 	f"<code>Сообщение принято:</code>\n\n{text}",
	# 	parse_mode="HTML"
	# )
	
	# await asyncio.sleep(1)
	#
	await last_msg.edit_text(text)
	
	os.remove(file_name_full)
	os.remove(file_name_full_converted)


if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)
