import logging
import os
import io
import uuid
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ContentType
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Установка ключа API OpenAI
openai_api_key = os.environ.get("OPENAI_TOKEN")
client_openai = OpenAI(api_key=openai_api_key)

# Инициализация бота
TOKEN = os.getenv('TG_BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Создаем папку для сохранения голосовых сообщений
os.makedirs('../voice', exist_ok=True)


# Обработчик команды /img
@dp.message_handler(commands=['img'])
async def handle_img_command(message: types.Message):
    try:
        # Отправляем промежуточное сообщение ожидания
        await bot.send_chat_action(message.chat.id, "typing")

        # Генерация изображения с использованием OpenAI API
        response_image = client_openai.images.generate(
	        model="dall-e-2",
	        prompt=message.get_args(),
	        n=1,
	        size="1024x1024"
        )

        image_url = response_image.data[0].url
        await message.answer_photo(image_url)

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /img: {e}")
        await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")


if __name__ == '__main__':
    # Запускаем бота
    executor.start_polling(dp, skip_updates=True)
