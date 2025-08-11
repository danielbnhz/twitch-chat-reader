import os
import asyncio
import datetime
from dotenv import load_dotenv
from twitchio.ext import commands
from textblob import TextBlob


load_dotenv()

TOKEN = os.getenv("TWITCH_TOKEN")
CHANNEL = os.getenv("TWITCH_CHANNEL")
BOT_NICK = os.getenv("BOT_NICK", "bot")
openai_api_key = os.getenv("OPENAI_API_KEY")


if not TOKEN or not CHANNEL:
    raise SystemExit("Please set TWITCH_TOKEN and TWITCH_CHANNEL in .env")

print("Loaded API Key:", openai_api_key[:8] + "..." if openai_api_key else "No key found")

chat_log = []


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TOKEN, prefix="!", initial_channels=[CHANNEL])

    async def event_ready(self):
        print(f"Connected — logged in as: {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return
         # Analyze sentiment
        analysis = TextBlob(message.content)
        polarity = analysis.sentiment.polarity  # float between -1 (negative) and 1 (positive)

        chat_log.append({
            "time": datetime.datetime.utcnow(),
            "user": message.author.name,
            "content": message.content
        })        

        print(f"{message.author.name}: {message.content} (Sentiment: {polarity:.2f})")
        await self.handle_commands(message)

if __name__ == "__main__":
    bot = Bot()
    bot.run()
