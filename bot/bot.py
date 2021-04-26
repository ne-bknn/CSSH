import io
import os

import asyncio

from aiogram import types, filters
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db import RedisDB
from keygen import KeyGenerator

redis = RedisDB.create("redis://localhost")
keygen = KeyGenerator()

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=["start"], state="*")
async def handler_greeting(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("I'm an authorization bot. Use /reg to register and get a private key or /gen to generate new key!")

@dp.message_handler(commands=["reg"], state="*")
async def handler_registration(message: types.Message, state: FSMContext):
    await state.finish()
    # step one - check whether already registered

    # step two - if not, check telegram username and suggest

    # step three - if not suitable or user do not want to use it, offer to enter valid

    # step four - register user with username, generate key

@dp.message_handler(commands=["gen"], state="*")
async def handler_regen(message: types.Message, state: FSMContext):
    await state.finish()
    # step one - check whether registered
    # if not, offer to register
    # if registered, update key and send new one
