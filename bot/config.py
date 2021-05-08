import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise Exception("No BOT_TOKEN provided")

DB_HOST = os.getenv("DB_HOST", "localhost:6379")

ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID is None:
    raise Exception("No ADMIN_ID provided")

DB_CONN = f"redis://{DB_HOST}/0"
