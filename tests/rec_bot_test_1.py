import asyncio
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

# Создаем папку, если ее нет
os.makedirs('../voice', exist_ok=True)
os.makedirs('../ready', exist_ok=True)


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
	# last_msg = await message.answer(
	# 	"<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
	# )
	
	await message.answer(
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
	
	# await asyncio.sleep(1)
	#
	# await last_msg.edit_text(text)
	
	os.remove(file_name_full)
	os.remove(file_name_full_converted)


# Обработчик callback-кнопки
@dp.callback_query_handler(lambda c: c.data.startswith('send_text:'))
async def process_callback_button(callback_query: types.CallbackQuery):
	_, text = callback_query.data.split(':')
	await bot.answer_callback_query(callback_query.id)
	await bot.send_message(callback_query.from_user.id, f"Вы выбрали отправку текста:\n{text}")
	await bot.edit_message_reply_markup(callback_query.from_user.id, callback_query.message.message_id)


if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)