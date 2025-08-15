from twitchio.ext import commands
from llama_cpp import Llama
import os
import time
from dotenv import load_dotenv
load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_NICK = os.getenv("BOT_NICK")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
MODEL_PATH = os.getenv("LLM_MODEL_PATH")

llm = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=1024)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, prefix="!", initial_channels=[TWITCH_CHANNEL])
        self.chat_buffer = []
        self.last_batch_time = time.time()
        self.batch_interval = 10
        self.batch_size = 5

    async def event_ready(self):
        print(f"Logged in as {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        self.chat_buffer.append(f"{message.author.name}: {message.content}")

        if len(self.chat_buffer) >= self.batch_size or \
           time.time() - self.last_batch_time >= self.batch_interval:
            await self.analyze_chat(self.chat_buffer[:])
            self.chat_buffer.clear()
            self.last_batch_time = time.time()

    async def analyze_chat(self, batch):
        prompt = (
            "You are a Twitch chat analyzer. Summarize the following messages, "
            "including main topics and overall tone. Respond only with a concise analysis:\n\n"
        )
        prompt += "\n".join(batch)
        response = llm(prompt, max_tokens=100)
        print("LLaMA Analysis:", response["choices"][0]["text"].strip())

if __name__ == "__main__":
    bot = Bot()
    bot.run()
