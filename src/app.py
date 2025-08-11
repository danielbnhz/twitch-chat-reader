import os
from twitchio.ext import commands
from dotenv import load_dotenv

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_NICK = os.getenv("BOT_NICK")  # Your bot's username
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")  # Channel to join

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            prefix="!",
            initial_channels=[TWITCH_CHANNEL]
        )

    async def event_ready(self):
        print(f"Logged in as | {self.nick}")

    async def event_message(self, message):
        # Ignore messages sent by the bot itself
        if message.author.name.lower() == TWITCH_NICK.lower():
            return

        print(f"{message.author.name}: {message.content}")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
