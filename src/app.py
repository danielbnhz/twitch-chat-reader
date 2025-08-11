import os
import threading
import time
from collections import deque
import asyncio
from twitchio.ext import commands
import openai  # make sure to `pip install openai twitchio`
from dotenv import load_dotenv

load_dotenv() 
# Load keys from environment variables or .env
TWITCH_TOKEN = os.getenv('TWITCH_TOKEN')  # OAuth token with chat:read
TWITCH_NICK = os.getenv('TWITCH_NICK')    # your bot's Twitch username
TWITCH_CHANNEL = os.getenv('TWITCH_CHANNEL')  # channel to join
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

MAX_MESSAGES = 100
chat_messages = deque(maxlen=MAX_MESSAGES)

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=TWITCH_TOKEN,
                         nick=TWITCH_NICK,
                         prefix='!',
                         initial_channels=[TWITCH_CHANNEL])

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        if message.echo:
            return
        print(f'[{message.author.name}]: {message.content}')
        chat_messages.append(message.content)
        await self.handle_commands(message)
client = OpenAI()

def openai_worker():
    while True:
        time.sleep(30)  # every 30 seconds
        if chat_messages:
            batch = list(chat_messages)
            print(f'Analyzing {len(batch)} messages...')
            prompt = "Analyze these Twitch chat messages:\n" + "\n".join(batch)
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant analyzing Twitch chat."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150
                )
                analysis = response.choices[0].message.content.strip()
                print("OpenAI analysis saved to analysis.txt")
                with open("analysis.txt", "w", encoding="utf-8") as f:
                    f.write(f"OpenAI analysis of last {len(batch)} messages:\n\n")
                    f.write(analysis)
                    f.write("\n")
            except Exception as e:
                print("OpenAI API error:", e)

if __name__ == "__main__":
    bot = Bot()

    # Start OpenAI worker in separate thread
    t = threading.Thread(target=openai_worker, daemon=True)
    t.start()

    # Run Twitch bot (asyncio event loop)
    bot.run()
