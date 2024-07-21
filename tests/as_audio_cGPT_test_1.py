import logging
import os
import io
import uuid
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ContentType
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Установка ключа API OpenAI
client = AsyncOpenAI(
	# This is the default and can be omitted
	api_key=os.environ.get("OPENAI_TOKEN"),
)

# Инициализация бота
TOKEN = os.getenv('TG_BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Создаем папку для сохранения голосовых сообщений
os.makedirs('../voice', exist_ok=True)


# Обработчик голосовых сообщений
@dp.message_handler(content_types=ContentType.VOICE)
async def handle_voice(message: types.Message):
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


if __name__ == '__main__':
	# Запускаем бота
	executor.start_polling(dp, skip_updates=True)
