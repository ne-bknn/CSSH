import io
import os
from secrets import token_urlsafe as password_generate
import re

from typing import Union, Optional, List
import logging

import asyncio

from aiogram import types, filters
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import ui
from db import RedisDB as InterfaceDB

BOT_TOKEN = os.environ["BOT_TOKEN"]

logging.basicConfig(level=logging.INFO)

db: InterfaceDB = None

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=["start"], state="*")
async def handler_greeting(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "I'm an authorization bot. Use /reg to register and get your credentials and /tasks get task list."
    )


@dp.message_handler(commands=["reg"], state="*")
async def handler_registration(message: types.Message, state: FSMContext):
    await state.finish()
    if await db.is_registered(message.from_user["id"]):
        await message.answer("You are already registered!")
        return

    username = message.from_user["username"]
    suggested_usernames = await ui.username_suggest(username)
    await ui.RegistrationStates.picking_username.set()
    keyboard = await ui.kb_username_picker(suggested_usernames)
    await message.answer("Lets choose your username", reply_markup=keyboard)

    # step four - register user with username, generate password

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("pick_username"), state=ui.RegistrationStates.picking_username)
async def handler_picker(callback_query: types.CallbackQuery, state: FSMContext):
    logging.info("Entered handler_picker") 
    await bot.answer_callback_query(callback_query.id)

    if await db.is_registered(callback_query.from_user["id"]):
        await callback_query.answer("You are already registered!", show_alert=True)
        return

    picked_username = callback_query.data.split(":")[1]

    # race protection, I guess... Just making it a little bit harder to race, but 
    # exploiting race now requires collaboration between two parties which make 
    # it impactless. I guess.
    if await db.contains(picked_username):
        await callback_query.answer("Somehow someone has this username, try another one", show_alert=True)
        return
    
    await db.create_user(callback_query.from_user["id"], picked_username)
    key = password_generate(16)
    await db.create_key(callback_query.from_user["id"], key)
    await callback_query.message.answer(f"Your password is: {key}")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("enter_username"), state=ui.RegistrationStates.picking_username)
async def handler_entering(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Enter your username:")
    await ui.RegistrationStates.entering_username.set()

@dp.message_handler(state=ui.RegistrationStates.entering_username)
async def handler_manual_username_picker(message: types.Message, state: FSMContext):
    username = message.text
    username_regex = "^[A-Za-z0-9_]{4,20}$"
    if not re.match(username_regex, username):
        await message.answer("Username does not match {username_regex}. Enter valid username")
        return

    if await db.contains(username):
        await message.answer("This username is already registered. Enter another one")
        return
    
    await db.create_user(message.from_user["id"], username)
    key = password_generate(16)
    await db.create_key(message.from_user["id"], key)
    await message.answer(f"Successfully registered your account! Your password is: {key}")
    await state.finish()

@dp.callback_query_handler(lambda c: True, state="*")
async def handler_fallback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    logging.warning(f"Received unhandled query! Data: {callback_query.data}")

async def setup_db_connection():
    global db
    db = await InterfaceDB.create("redis://localhost/0")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_db_connection())

    executor.start_polling(dp, skip_updates=True)

