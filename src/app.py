from twitchio.ext import commands
from llama_cpp import Llama
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

sys.path.append('../build')  # Adjust to where your compiled chat_stats module is
import chat_stats

# Twitch + model settings
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_NICK = os.getenv("BOT_NICK")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
MODEL_PATH = os.getenv("LLM_MODEL_PATH")

# LLaMA model + thread executor
llm = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=1024)
executor = ThreadPoolExecutor(max_workers=1)


MAX_PROMPT_TOKENS = 900  # leave some room for LLM output

def truncate_prompt(prompt, max_tokens=MAX_PROMPT_TOKENS):
    tokens = llm.tokenize(prompt.encode("utf-8"))
    if len(tokens) > max_tokens:
        tokens = tokens[-max_tokens:]  # keep last part
    return llm.detokenize(tokens).decode("utf-8")


async def analyze_with_llama(prompt):
    """Run LLaMA prompt in a background thread."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, lambda: llm(prompt, max_tokens=100)
    )
    return result["choices"][0]["text"].strip()


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, prefix="!", initial_channels=[TWITCH_CHANNEL])
        self.chat_buffer = []
        self.last_batch_time = time.time()
        self.batch_interval = 30  # seconds

    async def event_ready(self):
        print(f"Logged in as {self.nick}")
        self.loop.create_task(self.process_stats_periodically())

    async def event_message(self, message):
        if message.echo:
            return
        # Add message to buffer
        self.chat_buffer.append(f"{message.author.name}: {message.content}")

    async def process_stats_periodically(self):
        """Every batch_interval seconds, run C++ stats + AI summary silently."""
        while True:
            await asyncio.sleep(1)
            now = time.time()

            if now - self.last_batch_time >= self.batch_interval and self.chat_buffer:
                batch = self.chat_buffer[:]
                self.chat_buffer.clear()
                self.last_batch_time = now

                # Run C++ stats
                stats = chat_stats.analyze_chat(batch)
                for user, stat in stats.items():
                    avg_words = stat.avg_words
                    caps_ratio = stat.caps_ratio
                    print(f"{user}: avg_words={avg_words:.2f}, caps_ratio={caps_ratio:.2f}")

                # Run AI summary
                prompt = (
                    "You are a Twitch chat analyzer. Summarize the following messages, "
                    "including main topics and overall tone. Respond only with a concise analysis:\n\n"
                    + "\n".join(batch)
                )
                prompt = truncate_prompt(prompt)  # make sure it fits the model context
                ai_summary = await analyze_with_llama(prompt)
                print("LLaMA Analysis:", ai_summary)


if __name__ == "__main__":
    bot = Bot()
    bot.run()
