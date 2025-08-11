import os
import asyncio
import datetime
from dotenv import load_dotenv
from twitchio.ext import commands
from textblob import TextBlob
import threading
import openai

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

        print(f"{message.author.name}: {message.content} (Sentiment: {polarity:.2f}) \n \n")
        await self.handle_commands(message)
    async def analyze_chat(self):
        if not chat_log:
            print("No chat messages to analyze.")
            return

        conversation_text = "\n".join(
            f"{msg['user']}: {msg['content']}" for msg in chat_log
        )

        print("\n--- Sending chat to OpenAI for analysis ---")
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI assistant summarizing Twitch chat."},
                    {"role": "user", "content": f"Analyze the following chat messages:\n{conversation_text}"}
                ],
                max_tokens=150
            )
            analysis = response.choices[0].message.content
            print(f"--- Analysis ---\n{analysis}\n")
        except Exception as e:
            print(f"OpenAI API error: {e}")

        chat_log.clear()

# Function to listen for terminal input without blocking asyncio loop
def terminal_listener(bot: Bot):
    while True:
        cmd = input()
        if cmd.strip().lower() == "analyze":
            # Schedule the analyze_chat coroutine in the bot's event loop
            asyncio.run_coroutine_threadsafe(bot.analyze_chat(), bot.loop)

if __name__ == "__main__":
    bot = Bot()

    # Start terminal listener in a separate thread
    listener_thread = threading.Thread(target=terminal_listener, args=(bot,), daemon=True)
    listener_thread.start()

    bot.run()