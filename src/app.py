import os
import subprocess
import sys
import time
import socket
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from twitchio.ext import commands

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
from llama_cpp import Llama
llm = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=1024)
executor = ThreadPoolExecutor(max_workers=1)

MAX_PROMPT_TOKENS = 900

def truncate_prompt(prompt, max_tokens=MAX_PROMPT_TOKENS):
    tokens = llm.tokenize(prompt.encode("utf-8"))
    if len(tokens) > max_tokens:
        tokens = tokens[-max_tokens:]
    return llm.detokenize(tokens).decode("utf-8")

async def analyze_with_llama(prompt):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, lambda: llm(prompt, max_tokens=100)
    )
    return result["choices"][0]["text"].strip()

# --- TCP server for Rust GUI ---
def wait_for_gui(host="127.0.0.1", port=7879, timeout=10):
    print(f"Waiting for Rust GUI to connect on {host}:{port}...")
    start = time.time()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    server.settimeout(0.5)

    gui_conn = None
    while True:
        try:
            gui_conn, addr = server.accept()
            print(f"Rust GUI connected from {addr}")
            break
        except socket.timeout:
            if time.time() - start > timeout:
                raise TimeoutError("Rust GUI did not start in time")
    return gui_conn

# --- Twitch Bot ---
class Bot(commands.Bot):
    def __init__(self, gui_conn):
        super().__init__(token=TWITCH_TOKEN, prefix="!", initial_channels=[TWITCH_CHANNEL])
        self.gui_conn = gui_conn
        self.chat_buffer = []
        self.last_batch_time = time.time()
        self.batch_interval = 30

    def send_to_gui(self, msg_type: str, msg: str):
        try:
            payload = f"{msg_type}:{msg}\n".encode("utf-8")
            self.gui_conn.sendall(payload)
        except Exception as e:
            print("Failed to send to GUI:", e)

    async def event_ready(self):
        print(f"Logged in as {self.nick}")
        self.loop.create_task(self.process_stats_periodically())

    async def event_message(self, message):
        if message.echo:
            return
        msg_text = f"{message.author.name}: {message.content}"
        self.chat_buffer.append(msg_text)
        self.send_to_gui("CHAT", msg_text)

    async def process_stats_periodically(self):
        while True:
            await asyncio.sleep(1)
            now = time.time()
            if now - self.last_batch_time >= self.batch_interval and self.chat_buffer:
                batch = self.chat_buffer[:]
                self.chat_buffer.clear()
                self.last_batch_time = now

                # C++ stats
                stats = chat_stats.analyze_chat(batch)
                for user, stat in stats.items():
                    stat_msg = f"{user}: avg_words={stat.avg_words:.2f}, caps_ratio={stat.caps_ratio:.2f}"
                    self.send_to_gui("STATS", stat_msg)

                # LLM summary
                prompt = "Summarize the following chat messages:\n\n" + "\n".join(batch)
                prompt = truncate_prompt(prompt)
                ai_summary = await analyze_with_llama(prompt)
                self.send_to_gui("LLM", ai_summary)

# --- Main ---
if __name__ == "__main__":
    # Launch Rust GUI as a subprocess
    gui_path = os.path.join(os.path.dirname(__file__), "../rust_gui/target/release/rust_gui.exe")
    try:
        subprocess.Popen([gui_path])
        print("Launched Rust GUI...")
    except Exception as e:
        print("Failed to launch Rust GUI:", e)
        sys.exit(1)

    # Wait for Rust GUI connection
    try:
        gui_conn = wait_for_gui()
    except TimeoutError as e:
        print("Error:", e)
        sys.exit(1)

    # Start Twitch bot
    try:
        bot = Bot(gui_conn)
        bot.run()  # blocks until bot stops
    except Exception as e:
        print("Bot exited with error:", e)
        sys.exit(1)
