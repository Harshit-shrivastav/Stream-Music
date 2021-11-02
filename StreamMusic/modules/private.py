# StreamMusic (Telegram bot project )
# Copyright (C) 2021  Sadew Jayasekara

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
from StreamMusic.modules.msg import Messages as tr
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardButton
from pyrogram.types import Message
from StreamMusic.config import SOURCE_CODE
from StreamMusic.config import ASSISTANT_NAME
from StreamMusic.config import PROJECT_NAME
from StreamMusic.config import SUPPORT_GROUP
from StreamMusic.config import UPDATES_CHANNEL
from StreamMusic.config import BOT_USERNAME
logging.basicConfig(level=logging.INFO)

@Client.on_message(filters.private & filters.incoming & filters.command(['start']))
def _start(client, message):
    client.send_message(message.chat.id,
        text=tr.START_MSG.format(message.from_user.first_name, message.from_user.id),
        parse_mode="markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❰𝗔𝗱𝗱 𝗺𝗲 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗚𝗿𝗼𝘂𝗽❱", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
                [
                    InlineKeyboardButton(
                        "❰𝗢𝘄𝗻𝗲𝗿❱", url=f"https://t.me/ehsaasmusic_bot"), 
                    InlineKeyboardButton(
                        "❰𝗚𝗿𝗼𝘂𝗽❱", url=f"https://t.me/{SUPPORT_GROUP}")
                ],[
                    InlineKeyboardButton(
                        "❰𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀❱", url=f"https://telegra.ph/Army-music-commanda-11-02")
                ]
            ]
        ),
        reply_to_message_id=message.message_id
        )

@Client.on_message(filters.command("start") & ~filters.private & ~filters.channel)
async def gstart(_, message: Message):
    await message.reply_text(
        f"""🅷🅸, 🅴🅷🆂🅰🅰🅷 🅼🆄🆂🅸🅲 🅸🆂 🆁🆄🅽🅽🅸🅽🅶 🅽🅾🆆.""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❰𝗢𝘄𝗻𝗲𝗿❱", url=f"https://t.me/army0071"),
                    InlineKeyboardButton(
                        "❰𝗚𝗿𝗼𝘂𝗽❱", url=f"https://t.me/{SUPPORT_GROUP}")
                ]
            ]
        ),
    )


@Client.on_message(filters.private & filters.incoming & filters.command(['help']))
def _help(client, message):
    client.send_message(chat_id = message.chat.id,
        text = tr.HELP_MSG[1],
        parse_mode="markdown",
        disable_web_page_preview=True,
        disable_notification=True,
        reply_markup = InlineKeyboardMarkup(map(1)),
        reply_to_message_id = message.message_id
    )

help_callback_filter = filters.create(lambda _, __, query: query.data.startswith('help+'))

@Client.on_callback_query(help_callback_filter)
def help_answer(client, callback_query):
    chat_id = callback_query.from_user.id
    disable_web_page_preview=True
    message_id = callback_query.message.message_id
    msg = int(callback_query.data.split('+')[1])
    client.edit_message_text(chat_id=chat_id,    message_id=message_id,
        text=tr.HELP_MSG[msg],    reply_markup=InlineKeyboardMarkup(map(msg))
    )


def map(pos):
    if(pos==1):
        button = [
            [InlineKeyboardButton(text = '▶️', callback_data = "help+2")]
        ]
    elif(pos==len(tr.HELP_MSG)-1):
        url = f"https://t.me/{SUPPORT_GROUP}"
        button = [
            [InlineKeyboardButton("❰𝗔𝗱𝗱 𝗺𝗲 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗚𝗿𝗼𝘂𝗽❱", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton(text = '❰𝗢𝘄𝗻𝗲𝗿❱', url=f"https://t.me/army0071"),
             InlineKeyboardButton(text = '❰𝗚𝗿𝗼𝘂𝗽❱', url=f"https://t.me/{SUPPORT_GROUP}")],
            [InlineKeyboardButton(text = '❰𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀❱', url=f"https://telegra.ph/Army-music-commanda-11-02")],
            [InlineKeyboardButton(text = '◀️', callback_data = f"help+{pos-1}")]
        ]
    else:
        button = [
            [
                InlineKeyboardButton(text = '◀️', callback_data = f"help+{pos-1}"),
                InlineKeyboardButton(text = '▶️', callback_data = f"help+{pos+1}")
            ],
        ]
    return button

@Client.on_message(filters.command("help") & ~filters.private & ~filters.channel)
async def ghelp(_, message: Message):
    await message.reply_text(
        f"""**🙋‍♀️ 𝓗𝓮𝓵𝓵𝓸 𝓽𝓱𝓮𝓻𝓮! 𝓘 𝓬𝓪𝓷 𝓹𝓵𝓪𝔂 𝓶𝓾𝓼𝓲𝓬 𝓲𝓷 𝓽𝓱𝓮 𝓿𝓸𝓲𝓬𝓮 𝓬𝓱𝓪𝓽𝓼 𝓸𝓯 𝓽𝓮𝓵𝓮𝓰𝓻𝓪𝓶 𝓰𝓻𝓸𝓾𝓹𝓼 & 𝓬𝓱𝓪𝓷𝓷𝓮𝓵𝓼.**""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❰𝗖𝗹𝗶𝗰𝗸 𝗵𝗲𝗿𝗲 𝗳𝗼𝗿 𝗵𝗲𝗹𝗽❱", url=f"https://t.me/{BOT_USERNAME}?start"
                    )
                ]
            ]
        ),
    )

