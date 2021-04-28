from typing import List, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup

from db import RedisDB as InterfaceDB

### STATES
class RegistrationStates(StatesGroup):
    picking_username = State()
    entering_username = State()


### KEYBOARDS
async def change_keyboard(callback, keyboard, bot):
    await bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message["message_id"],
        reply_markup=keyboard,
    )


async def username_suggest(username: Optional[str]):
    """Validates, truncates, checks availability
    Probably should be a bit less dumb
    post: isinstance(__return__, list) and [isinstance(c, str) for c in __return__]
    """

    # this string should not be hardcoded
    db = await InterfaceDB.create_tmp("redis://localhost/0")

    suggested_usernames = []
    if username is None:
        await db.close()
        return suggested_usernames

    if await db.contains(username):
        await db.close()
        return suggested_usernames

    suggested_usernames.append(username[:20])
    await db.close()
    return suggested_usernames


async def kb_username_picker(usernames: List[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for username in usernames:
        keyboard.add(
            InlineKeyboardButton(username, callback_data=f"pick_username:{username}")
        )

    keyboard.add(
        InlineKeyboardButton("enter manually..", callback_data="enter_username")
    )

    return keyboard

async def kb_images_picker(page: int) -> Optional[InlineKeyboardMarkup]:
    keyboard = InlineKeyboardMarkup(row_width=1)
    db = await InterfaceDB.create_tmp("redis://localhost/0")

    images = await db.get_images()
    images_to_add = images[page*5:page*5+5]

    if page == 0 and len(images_to_add) == 0:
        await db.close()
        return None

    for image in images_to_add:
        keyboard.add(InlineKeyboardButton(image, callback_data=f"picked_image:{image}"))
    
    if not (len(images_to_add) < 5 or len(images[(page+1)*5:(page+1)*5+5]) == 0):
        keyboard.add(InlineKeyboardButton(">", callback_data=f"next_image_list:{page+1}"))

    if page != 0:
        keyboard.add(InlineKeyboardButton("<", callback_data=f"next_image_list:{page-1}"))
    
    await db.close()
    return keyboard
