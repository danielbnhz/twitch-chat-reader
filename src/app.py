import os
import asyncio
from twitchio.ext import commands
from dotenv import load_dotenv

load_dotenv()

ANALYSIS_FILE = "conversation_analysis.txt"
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_NICK = os.getenv("BOT_NICK")  # Your bot's username
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")  # Channel to join


async def query_ollama_async(prompt):
    process = await asyncio.create_subprocess_exec(
        "ollama", "run", "llama2", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Ollama error: {stderr.decode()}")
        return ""
    return stdout.decode().strip()


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, prefix="!", initial_channels=[TWITCH_CHANNEL])
        self.chat_log = []
        self.analysis_task = None

    async def event_ready(self):
        print(f"Logged in as {self.nick}")

    async def event_message(self, message):
        if message.author.name.lower() == TWITCH_NICK.lower():
            return

        print(f"{message.author.name}: {message.content}")
        self.chat_log.append(f"{message.author.name}: {message.content}")

        if len(self.chat_log) % 5 == 0:
            if self.analysis_task and not self.analysis_task.done():
                self.analysis_task.cancel()

            prompt = (
                "Analyze the following Twitch chat conversation so far and "
                "summarize the main themes and tone:\n\n"
                + "\n".join(self.chat_log)
            )
            self.analysis_task = asyncio.create_task(self.do_analysis(prompt))

        await self.handle_commands(message)

    async def do_analysis(self, prompt):
        analysis = await query_ollama_async(prompt)
        with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
            f.write(analysis)
        print("\n=== Updated chat analysis saved ===\n")


if __name__ == "__main__":
    bot = Bot()
    bot.run()
