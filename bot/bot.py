import io
import os
from secrets import token_urlsafe as password_generate

from typing import Union, Optional, List

import asyncio

from aiogram import types, filters
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from db import RedisDB

db = RedisDB.create("redis://localhost")

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

### STATES
class RegistrationStates:
    picking_username = State()
    entering_username = State()

### KEYBOARD FACTORIES
async def kb_username_picker(usernames: List[str]):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for username in usernames:
        keyboard.add(InlineKeyboardButton(username, callback_data=f"pick_username:{username}"))
    
    keyboard.add(InlineKeyboardButton(username, callback_data="enter_username"))

@dp.message_handler(commands=["start"], state="*")
async def handler_greeting(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "I'm an authorization bot. Use /reg to register and get your credentials and /tasks get task list."
    )

#
async def username_suggest(username: Optional[str]):
    """Validates, truncates, checks availability
    Probably should be a bit less dumb"""
    suggested_usernames = []
    if username is None:
        return suggested_usernames

    if await db.contains(username):
        return suggested_usernames

    suggested_usernames.append(username[:20])
    return suggested_usernames


@dp.message_handler(commands=["reg"], state="*")
async def handler_registration(message: types.Message, state: FSMContext):
    await state.finish()
    if await db.is_registered(message.from_user["id"]):
        await message.answer("You are already registered!")
        return

    username = message.from_user["username"]
    suggested_usernames = await username_suggest(username)

    # step four - register user with username, generate key

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("pick_username"))
async def handler_picker(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    if await db.is_registered(callback_query.from_user["id"]):
        await callback_query.answer("You are already registered!")
        return

    picked_username = callback_query.data.split(":")[1]
    await state.finish()

    # race protection, I guess... Just making it a little bit harder to race, but 
    # exploiting race now requires collaboration between two parties which make 
    # it impactless. I guess.
    if await db.contains(picked_username):
        callback_query.answer("Failed to register with given username, try again(")
        return
    
    await db.create_user(callback_query.from_user["id"], picked_username)
    key = password_generate(16)
    await db.create_key(callback_query.from_user["id"], key)
    await callback_query.answer(f"Your password is: {key}")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("enter_username"))
async def handler_entering(callback_query: types.CallbackQuery, state: FSMContext):
    pass

@dp.message_handler(commands=["gen"], state="*")
async def handler_regen(message: types.Message, state: FSMContext):
    await state.finish()
    # step one - check whether registered
    # if not, offer to register
    # if registered, update key and send new one
