import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise Exception("No BOT_TOKEN provided")

DB_HOST = os.getenv("DB_HOST", "localhost:6379")

DB_CONN = f"redis://{DB_HOST}/0"
