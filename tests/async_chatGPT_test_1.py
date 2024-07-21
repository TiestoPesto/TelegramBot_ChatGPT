import os
from dotenv import load_dotenv, find_dotenv
import asyncio
from openai import AsyncOpenAI

load_dotenv(find_dotenv())

client = AsyncOpenAI(
	# This is the default and can be omitted
	api_key=os.environ.get("OPENAI_TOKEN"),
)


async def main():
	chat_completion = await client.chat.completions.create(
		messages=[
			{
				"role": "user",
				"content": 'Привет как дела?',
			}
		],
		model="gpt-3.5-turbo",
	)
	
	print(chat_completion.choices[0].message.content)

if __name__ == '__main__':
	asyncio.run(main())
