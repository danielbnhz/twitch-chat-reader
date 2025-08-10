import os
from dotenv import load_dotenv
from twitchio.ext import commands

load_dotenv()

TOKEN = os.getenv("TWITCH_TOKEN")
CHANNEL = os.getenv("TWITCH_CHANNEL")
BOT_NICK = os.getenv("BOT_NICK", "bot")

if not TOKEN or not CHANNEL:
    raise SystemExit("Please set TWITCH_TOKEN and TWITCH_CHANNEL in .env")

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TOKEN, prefix="!", initial_channels=[CHANNEL])

    async def event_ready(self):
        print(f"Connected — logged in as: {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return
        print(f"{message.author.name}: {message.content}")
        await self.handle_commands(message)

if __name__ == "__main__":
    bot = Bot()
    bot.run()
