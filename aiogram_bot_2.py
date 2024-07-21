import asyncio
import logging
import os
import uuid
from dotenv import load_dotenv, find_dotenv
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from openai import AsyncOpenAI
import speech_recognition as sr


load_dotenv(find_dotenv())
language = 'ru_RU'

API_TOKEN = os.getenv('TG_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

# Установка ключа API OpenAI
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_TOKEN"))

# Создание объекта бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создание объекта обработки голоса
recognizer = sr.Recognizer()

# Настройка уровня логирования
logging.basicConfig(level=logging.INFO)

# Создание папок, если их нет
os.makedirs('./voice', exist_ok=True)
os.makedirs('./ready', exist_ok=True)

# Установка хедеров
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'}


async def recognize_voice(filename):
    with sr.AudioFile(filename) as source:
        audio_text = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio_text, language=language)
            logging.info('Перевод аудио в текст: %s', text)
            return text
        except Exception as e:
            logging.error('Ошибка при распознавании речи: %s', e)
            return "Извините, скажите еще раз"


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
        if chat_member.is_chat_member():
            welcome_text = (
                f"Привет, {message.from_user.first_name}! Я бот на базе ChatGPT, готовый помочь вам. "
                f"Просто отправьте мне ваш вопрос, и я постараюсь вам ответить."
            )
            await bot.send_chat_action(message.chat.id, "typing")
            last_msg = await message.answer("<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML")
            await asyncio.sleep(2)
            await last_msg.edit_text(welcome_text)
        else:
            await message.answer("Для безлимитного использования бота ChatGPT, подпишитесь на наш канал: "
                                 + CHANNEL_USERNAME)
    except Exception as e:
        logging.error("Ошибка старта бота: %s", e)
        await message.answer("Произошла ошибка. Попробуйте еще раз позже.")


@dp.message_handler(commands=["help"])
async def send_start(message: types.Message):
    text = """Чтобы начать взаимодействие с ChatGPT без ограничения, подпишитесь на наш канал  {} и отправьте сообщение, и бот ответит вам.

Вы можете задавать ему любые вопросы, он обычно отвечает на них адекватно и быстро.

Также вы можете использовать бота для выполнения различных задач, например, он может вывести расписание фильмов, погоду, новости, анекдоты и многое другое.

Кроме того, ChatGPT может быть использован для проведения небольших игр и конкурсов с пользователями.

Возможности бота очень широки, и вы можете экспериментировать и сами пробовать всевозможные примеры работы с ним. Не стесняйтесь обращаться к ChatGPT за помощью, он всегда готов вам помочь!

👋Если вопрос касается сотрудничества, обратитесь к - @gpt_dim
""".format(CHANNEL_USERNAME)
    await bot.send_chat_action(message.chat.id, "typing")
    last_msg = await message.answer("<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML")
    await asyncio.sleep(2)
    await last_msg.edit_text(text)


@dp.message_handler(content_types=ContentType.VOICE)
async def handle_voice(message: types.Message):
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
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

                downloaded_bytes = downloaded_file.read()

                with open(file_name_full, 'wb') as new_file:
                    new_file.write(downloaded_bytes)

                os.system("ffmpeg -i " + file_name_full + "  " + file_name_full_converted)
                text = await recognize_voice(file_name_full_converted)

                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("Отправить Говоруше?", callback_data="send_message"))

                await last_msg.edit_text(text=text, reply_markup=keyboard)

                os.remove(file_name_full)
                os.remove(file_name_full_converted)

            except Exception as e:
                logging.error("Ошибка в голосовом сообщении: %s", e)
                await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")

        else:
            await message.answer("Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
    except Exception as e:
        logging.error("An error occurred: %s", e)
        await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")


@dp.message_handler()
async def handle_messages(message: types.Message):
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
        if chat_member.is_chat_member():
            logging.info("Сообщение от %s: %s", message.from_user.username, message.text)
            await bot.send_chat_action(message.chat.id, "typing")
            last_msg = await message.answer("<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML")

            chat_completion = await client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": message.text,
                    }
                ],
                model="gpt-3.5-turbo",
            )

            await last_msg.edit_text(chat_completion.choices[0].message.content)

        else:
            await message.answer("Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)
    except Exception as e:
        logging.error("An error occurred: %s", e)
        await message.answer("Извините, произошла ошибка. Мы работаем над решением проблемы.")


@dp.callback_query_handler(lambda callback_query: callback_query.data == "send_message")
async def send_message(callback_query: types.CallbackQuery):
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, callback_query.from_user.id)
        if chat_member.is_chat_member():
            await bot.send_chat_action(callback_query.message.chat.id, "typing")
            last_msg = await callback_query.message.answer("Сообщение принято. Ждем ответа от Говоруши...")
            logging.info("Сообщение от %s: %s", callback_query.from_user.username, callback_query.message.text)

            chat_completion = await client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": callback_query.message.text,
                    }
                ],
                model="gpt-3.5-turbo",
            )

            await last_msg.edit_text(chat_completion.choices[0].message.content)

        else:
            await bot.send_message(callback_query.message.chat.id,
                                   "Для использования этой команды, подпишитесь на наш канал." + CHANNEL_USERNAME)

    except Exception as e:
        logging.error("An error occurred: %s", e)
        await bot.send_message(callback_query.message.chat.id,
                               "Извините, произошла ошибка. Мы работаем над решением проблемы.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
