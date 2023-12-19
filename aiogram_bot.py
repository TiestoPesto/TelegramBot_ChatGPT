"""
Данная версия бота написанная на асинхронной библиотеке AIogram.
Данная версия так же общается с использованием ChatGPT
"""

# подключаем библиотеки
import openai
from aiogram import Bot, types, Dispatcher, executor
import config

# Установка ключа API OpenAI
openai.api_key = config.OPENAI_TOKEN

# Создание объекта бота
bot = Bot(token=config.TG_BOT_TOKEN)
dp = Dispatcher(bot)

# Включение long polling
executor.start_polling(dp, skip_updates=True)

# Обработчик старта бота и приветствия
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    welcome_text = (
        "Привет! Я бот, готовый помочь вам. Просто отправьте мне ваш вопрос, и я постараюсь вам ответить."
    )
    await message.answer(welcome_text)

# Обработчик всех сообщений
@dp.message_handler()
async def handle_messages(message: types.Message):
    try:
        # Используйте openai.Completion.create вместо openai.completions.create
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=message.text,
            temperature=1,
            max_tokens=1123,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        # Вместо response['choices'][0]['text'], используйте response.choices[0].text
        await message.answer(response.choices[0].text)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
