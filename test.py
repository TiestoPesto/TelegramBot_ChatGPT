from aiogram import Bot, types, Dispatcher, executor
import config
from dotenv import load_dotenv
import os


# token = '5151246364:AAH0LuObpxcxEdGXLdM8y-kooa9ep6wuzlA'
# Создание объекта бота
load_dotenv()
bot = Bot(token=os.getenv('TG_BOT_TOKEN'))
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(msg: types.Message):
    await msg.answer(f'Привет, {msg.from_user.first_name}')
    
@dp.message_handler(content_types=['text'])
async def get_text_messages(msg: types.Message):
   if msg.text.lower() == 'привет':
       await msg.answer('Привет!')
   else:
       await msg.answer('Не понимаю, что это значит.')

# Включение long polling
executor.start_polling(dp, skip_updates=True)