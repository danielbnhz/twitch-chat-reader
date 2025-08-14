import os
import time
import asyncio
from twitchio.ext import commands
from multiprocessing import Process, Queue
from dotenv import load_dotenv
load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_NICK = os.getenv("BOT_NICK")  # Your bot's username
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")  # Channel to join
model_path = os.getenv("LLM_MODEL_PATH")


def llama_worker(input_q, output_q):
    from llama_cpp import Llama
    
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1,     # put as many layers on GPU as possible
        n_ctx=1024           # adjust based on VRAM
    )
    
    while True:
        batch = input_q.get()
        if batch == "STOP":
            break

        prompt = (
            "You are a Twitch chat analyzer. Summarize the following messages, "
            "including main topics and overall tone. Respond only with a concise analysis:\n\n"
        )
        prompt += "\n".join(batch)
        #print(f"[LLaMA Worker] Processing batch: {prompt}")
        
        response = llm(prompt, max_tokens=100)
        print(response["choices"][0]["text"].strip())


# ------------------------------------------
# Twitch Bot
# ------------------------------------------
class Bot(commands.Bot):
    def __init__(self, in_q, out_q):
        super().__init__(
            token=TWITCH_TOKEN,
            prefix="!",
            initial_channels=[TWITCH_CHANNEL]
        )
        self.in_q = in_q
        self.out_q = out_q
        self.chat_buffer = []
        self.last_batch_time = time.time()
        self.batch_interval = 10  # seconds
        self.batch_size = 5       # messages

    async def event_ready(self):
        print(f"Logged in as {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        self.chat_buffer.append(f"{message.author.name}: {message.content}")

        # Send batch if size or time threshold is met
        if len(self.chat_buffer) >= self.batch_size or \
           time.time() - self.last_batch_time >= self.batch_interval:
            self.in_q.put(self.chat_buffer[:])
            self.chat_buffer.clear()
            self.last_batch_time = time.time()

        # Check if LLaMA has responded
        await self.check_llama_responses()

    async def check_llama_responses(self):
        while not self.out_q.empty():
            response = self.out_q.get()
            #await self.connected_channels[0].send(f"LLaMA: {response}")
            print(f"LLaMA would respond: {response}")

# ------------------------------------------
# Main Entry
# ------------------------------------------
if __name__ == "__main__":
    in_q = Queue()
    out_q = Queue()

    # Start LLaMA process
    p = Process(target=llama_worker, args=(in_q, out_q))
    p.start()

    # Start Twitch bot
    bot = Bot(in_q, out_q)
    try:
        bot.run()
    finally:
        in_q.put("STOP")
        p.join()
