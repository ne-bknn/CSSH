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


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith("pick_username"),
    state=ui.RegistrationStates.picking_username,
)
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
        await callback_query.answer(
            "Somehow someone has this username, try another one", show_alert=True
        )
        return

    # TODO: DRY, markup
    await db.create_user(callback_query.from_user["id"], picked_username)
    key = password_generate(16)
    await db.create_key(callback_query.from_user["id"], key)
    await callback_query.message.answer(
        f"Successfully registered your account! Your password is: {key}"
    )
    await state.finish()


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith("enter_username"),
    state=ui.RegistrationStates.picking_username,
)
async def handler_entering(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Enter your username:")
    await ui.RegistrationStates.entering_username.set()


@dp.message_handler(state=ui.RegistrationStates.entering_username)
async def handler_manual_username_picker(message: types.Message, state: FSMContext):
    username = message.text
    username_regex = "^[A-Za-z0-9_]{4,20}$"
    if not re.match(username_regex, username):
        # TODO: markup
        await message.answer(
            f"Username does not match {username_regex}. Enter valid username"
        )
        return

    if await db.contains(username):
        await message.answer("This username is already registered. Enter another one")
        return

    # TODO: Dry, markup
    await db.create_user(message.from_user["id"], username)
    key = password_generate(16)
    await db.create_key(message.from_user["id"], key)
    await message.answer(
        f"Successfully registered your account! Your password is: {key}"
    )
    await state.finish()


@dp.message_handler(commands=["creds"])
async def handler_creds(message: types.Message, state: FSMContext):
    username = await db.get_username(message.from_user["id"])

    if username is None:
        await message.answer("You have to be registered to view creds! Use /reg")
        return
    
    # TODO: this should be done in db lib
    username = username.decode()

    password = (await db.get_secret(message.from_user["id"])).decode()
    await message.answer(f"Username: {username}\nPassword: {password}")


@dp.message_handler(commands=["add_image"])
async def handler_add_image(message: types.Message):
    if str(message.from_user["id"]) != "523549854":
        logging.warning(
            f"An attempt to use admin's commands by {message.from_user['id']}"
        )
        return

    l = message.text.split(" ")
    if len(l) != 2:
        await message.answer("I do not understand((")
        return

    imagename = l[1]
    imagename_regex = "^[A-Za-z0-9_]{3,20}$"
    if not re.match(imagename_regex, imagename):
        await message.answer(f"Imagename does not match regex")
        return

    await db.add_image(imagename)
    await message.answer("Done")


@dp.message_handler(commands=["del_image"])
async def handler_add_image(message: types.Message):
    if str(message.from_user["id"]) != "523549854":
        logging.warning(
            f"An attempt to use admin's commands by {message.from_user['id']}"
        )
        return

    l = message.text.split(" ")
    if len(l) != 2:
        await message.answer("I do not understand((")
        return

    imagename = l[1]

    await db.del_image(imagename)
    await message.answer("Done")


@dp.message_handler(commands=["images"])
async def handler_get_images(message: types.Message):
    # TODO: this one should return keyboard
    if not await db.is_registered(message.from_user["id"]):
        await message.answer("You have to be registered to view images!")
        return

    keyboard = await ui.kb_images_picker(0)


    if keyboard is None:
        await message.answer("No images yet")
    else:
        await message.answer(
            "Available images:", reply_markup=keyboard
        )

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("picked_image:"), state="*")
async def handler_image_picking(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    imagename = callback_query.data.split(":")[-1]
    if not await db.contains_image(imagename):
        logging.warning(f"Someone attempted to switch to nonexistent image. User's id: {callback_query.from_user['id']}")
        await callback_query.message.answer("This image is unaccessible")

    await set_image(callback_query.from_user["id"], imagename)
    await callback_query.message.answer(f"Successfully changed your image to {imagename}")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("next_image_list:"), state="*")
async def hanlder_image_next(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    page = int(callback_query.data.split(":")[-1])
    keyboard = await ui.kb_images_picker(page)
    await ui.change_keyboard(callback_query, keyboard, bot)

async def setup_db_connection():
    global db
    db = await InterfaceDB.create("redis://localhost/0")



@dp.callback_query_handler(lambda c: True, state="*")
async def handler_fallback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    logging.warning(f"Received unhandled query! Data: {callback_query.data}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_db_connection())

    executor.start_polling(dp, skip_updates=True)
