# StreamMusic (Telegram bot project)
# Copyright (C) 2021  Sadew Jayasekara
# Copyright (C) 2021  TheHamkerCat (Python_ARQ)
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


import json
import os
from os import path
from typing import Callable

import aiofiles
import aiohttp
import ffmpeg
import requests
import wget
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Voice
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import Message
from Python_ARQ import ARQ
from youtube_search import YoutubeSearch

from StreamMusic.config import ARQ_API_KEY
from StreamMusic.config import BOT_NAME as bn
from StreamMusic.config import DURATION_LIMIT
from StreamMusic.config import UPDATES_CHANNEL as updateschannel
from StreamMusic.config import que
from StreamMusic.function.admins import admins as a
from StreamMusic.helpers.admins import get_administrators
from StreamMusic.helpers.channelmusic import get_chat_id
from StreamMusic.helpers.errors import DurationLimitError
from StreamMusic.helpers.decorators import errors
from StreamMusic.helpers.decorators import authorized_users_only
from StreamMusic.helpers.filters import command
from StreamMusic.helpers.filters import other_filters
from StreamMusic.helpers.gets import get_file_name
from StreamMusic.services.callsmusic import callsmusic
from StreamMusic.services.callsmusic import client as USER
from StreamMusic.services.converter.converter import convert
from StreamMusic.services.downloaders import youtube
from StreamMusic.services.queues import queues

aiohttpsession = aiohttp.ClientSession()
chat_id = None
arq = ARQ("https://thearq.tech", ARQ_API_KEY, aiohttpsession)
DISABLED_GROUPS = []
useer ="NaN"
def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("You ain't allowed!", show_alert=True)
            return

    return decorator


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", format="s16le", acodec="pcm_s16le", ac=2, ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("./etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 32)
    draw.text((205, 550), f"Title: {title}", (51, 215, 255), font=font)
    draw.text((205, 590), f"Duration: {duration}", (255, 255, 255), font=font)
    draw.text((205, 630), f"Views: {views}", (255, 255, 255), font=font)
    draw.text(
        (205, 670),
        f"Added By: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return    
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("Player is idle")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "𝐍𝐨𝐰 𝐩𝐥𝐚𝐲𝐢𝐧𝐠 🎵 𝐢𝐧 **{}**".format(message.chat.title)
    msg += "\n- " + now_playing
    msg += "\n- 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**Queue**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n- **{name}**"
            msg += f"\n- 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 {usr}\n"
    await message.reply_text(msg)


# ============================= Settings =========================================


def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.active_chats:
        # if chat.id in active_chats:
        stats = "Settings of **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "𝐕𝐨𝐥𝐮𝐦𝐞 : {}%\n".format(vol)
            stats += "𝐒𝐨𝐧𝐠𝐬 𝐢𝐧 𝐪𝐮𝐞𝐮𝐞 : `{}`\n".format(len(que))
            stats += "𝐍𝐨𝐰 𝐏𝐥𝐚𝐲𝐢𝐧𝐠 : **{}**\n".format(queue[0][0])
            stats += "𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 : {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats


def r_ply(type_):
    if type_ == "play":
        pass
    else:
        pass
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏹", "leave"),
                InlineKeyboardButton("⏸", "puse"),
                InlineKeyboardButton("▶️", "resume"),
                InlineKeyboardButton("⏭", "skip"),
            ],
            [
                InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", "playlist"),
            ],
            [InlineKeyboardButton("❰𝗖𝗹𝗼𝘀𝗲❱", "cls")],
        ]
    )
    return mar


@Client.on_message(filters.command("current") & filters.group & ~filters.edited)
async def ee(client, message):
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("ɴᴏ 🎧 ᴠᴄ ɪɴꜱᴛᴀɴᴄᴇꜱ 🏃 ʀᴜɴɴɪɴɢ ɪɴ ᴛʜɪꜱ 🗨️ ᴄʜᴀᴛ")


@Client.on_message(filters.command("player") & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    if message.chat.id in DISABLED_GROUPS:
        await message.reply("𝑀𝓊𝓈𝒾𝒸 𝒫𝓁𝒶𝓎𝑒𝓇 𝒾𝓈 𝒟𝒾𝓈𝒶𝒷𝓁𝑒𝒹")
        return    
    playing = None
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        playing = True
    queue = que.get(chat_id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))

        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("𝗡𝗼 𝗩𝗖 𝗶𝗻𝘀𝘁𝗮𝗻𝗰𝗲𝘀 𝗿𝘂𝗻𝗻𝗶𝗻𝗴 𝗶𝗻 𝘁𝗵𝗶𝘀 𝗰𝗵𝗮𝘁")


@Client.on_message(
    filters.command("musicplayer") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "I only recognize `/musicplayer on` and /musicplayer `off only`"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await message.reply("`Processing...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("𝗠𝘂𝘀𝗶𝗰 𝗣𝗹𝗮𝘆𝗲𝗿 🎵 𝗶𝘀 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗲𝗱 𝗜𝗻 𝗧𝗵𝗶𝘀 𝗖𝗵𝗮𝘁 🗨️")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"𝓜𝓾𝓼𝓲𝓬 𝓟𝓵𝓪𝔂𝓮𝓻 𝓢𝓾𝓬𝓬𝓮𝓼𝓼𝓯𝓾𝓵𝓵𝔂 𝓔𝓷𝓪𝓫𝓵𝓮𝓭 𝓕𝓸𝓻 𝓤𝓼𝓮𝓻𝓼 𝓘𝓷 𝓣𝓱𝓮 𝓒𝓱𝓪𝓽 {message.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await message.reply("`Processing...`")
        
        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("Music Player Already turned off In This Chat")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"Music Player Successfully Deactivated For Users In The Chat {message.chat.id}"
        )
    else:
        await message.reply_text(
            "I only recognize `/musicplayer on` and /musicplayer `off only`"
        )    
        

@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):
    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("Player is idle")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**𝐍𝐨𝐰 𝐩𝐥𝐚𝐲𝐢𝐧𝐠 𝐢𝐧** {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Queue**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- **{name}**"
                msg += f"\n- 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 {usr}\n"
        await cb.message.edit(msg)


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|pause|skip|leave|puse|resume|menu|cls)$")
)
@cb_admin_check
async def m_cb(b, cb):
    global que
    if (
        cb.message.chat.title.startswith("Channel Music: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "paused"
        ):
            await cb.answer("Chat is not connected!", show_alert=True)
        else:
            callsmusic.pause(chet_id)
            await cb.answer("Music Paused!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "play":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "playing"
        ):
            await cb.answer("Chat is not connected!", show_alert=True)
        else:
            callsmusic.resume(chet_id)
            await cb.answer("Music Resumed!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("pause")
            )

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("Player is idle")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**𝐍𝐨𝐰 𝐩𝐥𝐚𝐲𝐢𝐧𝐠 𝐢𝐧** {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Queue**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- **{name}**"
                msg += f"\n- 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 **{usr}**\n"
        await cb.message.edit(msg)

    elif type_ == "resume":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "playing"
        ):
            await cb.answer("Chat is not connected or already playng", show_alert=True)
        else:
            callsmusic.resume(chet_id)
            await cb.answer("Music Resumed!")
    elif type_ == "puse":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "paused"
        ):
            await cb.answer("Chat is not connected or already paused", show_alert=True)
        else:
            callsmusic.pause(chet_id)
            await cb.answer("Music Paused!")
    elif type_ == "cls":
        await cb.answer("Closed menu")
        await cb.message.delete()

    elif type_ == "menu":
        stats = updated_stats(cb.message.chat, qeue)
        await cb.answer("Menu opened")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏹", "leave"),
                    InlineKeyboardButton("⏸", "puse"),
                    InlineKeyboardButton("▶️", "resume"),
                    InlineKeyboardButton("⏭", "skip"),
                ],
                [
                    InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", "playlist"),
                ],
                [InlineKeyboardButton("❰𝗖𝗹𝗼𝘀𝗲❱", "cls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)
    elif type_ == "skip":
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.active_chats:
            await cb.answer("Chat is not connected!", show_alert=True)
        else:
            queues.task_done(chet_id)
            if queues.is_empty(chet_id):
                callsmusic.stop(chet_id)
                await cb.message.edit("- No More Playlist..\n- Leaving VC!")
            else:
                await callsmusic.set_stream(
                    chet_id, queues.get(chet_id)["file"]
                )
                await cb.answer("Skipped")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"- Skipped track\n- Now Playing **{qeue[0][0]}**"
                )

    else:
        if chet_id in callsmusic.active_chats:
            try:
               queues.clear(chet_id)
            except QueueEmpty:
                pass

            await callsmusic.stop(chet_id)
            await cb.message.edit("Successfully Left the Chat!")
        else:
            await cb.answer("Chat is not connected!", show_alert=True)


@Client.on_message(command("play") & other_filters)
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return    
    lel = await message.reply("🎵 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Remember to add helper to your channel</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Add me as admin of yor group first</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "I joined this group for playing music in VC"
                    )
                    await lel.edit(
                        "<b>helper userbot joined your chat</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} couldn't join your group due to heavy requests for userbot! Make sure user is not banned in group."
                        "\n\nOr manually add assistant to your Group and try again</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot not in this chat, Ask admin to send /play command for first time or add {user.first_name} manually</i>"
        )
        return
    text_links=None
    await lel.edit("𝐅𝐢𝐧𝐝𝐢𝐧𝐠 💫 𝐓𝐡𝐞 𝐒𝐨𝐧𝐠 🎧 𝐅𝐫𝐨𝐦 𝗔𝗿𝗺𝘆 ❤️ 𝐒𝐞𝐫𝐯𝐞𝐫 🌎...'")
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message.entities:
            entities = message.reply_to_message.entities + entities
        elif message.reply_to_message.caption_entities:
            entities = message.reply_to_message.entities + entities
        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ 𝗩𝗶𝗱𝗲𝗼𝘀 𝗹𝗼𝗻𝗴𝗲𝗿 𝘁𝗵𝗮𝗻 {DURATION_LIMIT} 𝗺𝗶𝗻𝘂𝘁𝗲(𝘀) 𝗮𝗿𝗲𝗻'𝘁 𝗮𝗹𝗹𝗼𝘄𝗲𝗱 𝘁𝗼 𝗽𝗹𝗮𝘆!"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", callback_data="playlist"),
                    InlineKeyboardButton("❰𝗠𝗲𝗻𝘂 ⏯❱ ", callback_data="menu"),
                ],
                [InlineKeyboardButton(text="❰𝗖𝗹𝗼𝘀𝗲❱", callback_data="cls")],
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://toppng.com/uploads/preview/and-blank-effect-transparent-11546868080xgtiz6hxid.png"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "Locally added"
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("🎵 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "𝗦𝗼𝗻𝗴 🎵 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱.𝗧𝗿𝘆 𝗮𝗻𝗼𝘁𝗵𝗲𝗿 𝘀𝗼𝗻𝗴 🎵 𝗼𝗿 𝗺𝗮𝘆𝗯𝗲 𝘀𝗽𝗲𝗹𝗹 ✍️ 𝗶𝘁 𝗽𝗿𝗼𝗽𝗲𝗿𝗹𝘆."
            )
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", callback_data="playlist"),
                    InlineKeyboardButton("❰𝗠𝗲𝗻𝘂 ⏯❱", callback_data="menu"),
                ],
                [
                    InlineKeyboardButton(text="❰𝗬𝗼𝘂𝘁𝘂𝗯𝗲❱", url=f"{url}"),
                    InlineKeyboardButton(text="❰𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱❱", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="❰𝗖𝗹𝗼𝘀𝗲❱", callback_data="cls")],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        await lel.edit("🎵 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        
        try:
          results = YoutubeSearch(query, max_results=5).to_dict()
        except:
          await lel.edit("Give me something to play")
        # Looks like hell. Aren't it?? FUCK OFF
        try:
            toxxt = "✌**𝗪𝗵𝗮𝘁'𝘀 𝗧𝗵𝗲 ❤️ 𝗦𝗼𝗻𝗴 🎶 𝗬𝗼𝘂 😎 𝗪𝗮𝗻𝘁 𝗧𝗼 𝗣𝗹𝗮𝘆 🧿🤟**\n\n"
            j = 0
            useer=user_name
            emojilist = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣",]

            while j < 5:
                toxxt += f"{emojilist[j]} <b>Title - [{results[j]['title']}](https://youtube.com{results[j]['url_suffix']})</b>\n"
                toxxt += f" ╚ <b>Duration</b> - {results[j]['duration']}\n"
                toxxt += f" ╚ <b>Views</b> - {results[j]['views']}\n"
                toxxt += f" ╚ <b>Channel</b> - {results[j]['channel']}\n\n"

                j += 1            
            koyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1️⃣", callback_data=f'plll 0|{query}|{user_id}'),
                        InlineKeyboardButton("2️⃣", callback_data=f'plll 1|{query}|{user_id}'),
                        InlineKeyboardButton("3️⃣", callback_data=f'plll 2|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton("4️⃣", callback_data=f'plll 3|{query}|{user_id}'),
                        InlineKeyboardButton("5️⃣", callback_data=f'plll 4|{query}|{user_id}'),
                    ],
                    [InlineKeyboardButton(text="❌", callback_data="cls")],
                ]
            )       
            await lel.edit(toxxt,reply_markup=koyboard,disable_web_page_preview=True)
            # WHY PEOPLE ALWAYS LOVE PORN ?? (A point to think)
            return
            # Returning to pornhub
        except:
            await lel.edit("No Enough results to choose.. Starting direct play..")
                        
            # print(results)
            try:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:40]
                thumbnail = results[0]["thumbnails"][0]
                thumb_name = f"thumb{title}.jpg"
                thumb = requests.get(thumbnail, allow_redirects=True)
                open(thumb_name, "wb").write(thumb.content)
                duration = results[0]["duration"]
                results[0]["url_suffix"]
                views = results[0]["views"]

            except Exception as e:
                await lel.edit(
                    "𝗦𝗼𝗻𝗴 🎵 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱.𝗧𝗿𝘆 𝗮𝗻𝗼𝘁𝗵𝗲𝗿 𝘀𝗼𝗻𝗴 🎵 𝗼𝗿 𝗺𝗮𝘆𝗯𝗲 𝘀𝗽𝗲𝗹𝗹 ✍️ 𝗶𝘁 𝗽𝗿𝗼𝗽𝗲𝗿𝗹𝘆"
                )
                print(str(e))
                return
            dlurl=url
            dlurl=dlurl.replace("youtube","youtubepp")
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", callback_data="playlist"),
                        InlineKeyboardButton("❰𝗠𝗲𝗻𝘂 ⏯❱", callback_data="menu"),
                    ],
                    [
                        InlineKeyboardButton(text="❰𝗬𝗼𝘂𝘁𝘂𝗯𝗲❱", url=f"{url}"),
                        InlineKeyboardButton(text="❰𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱❱", url=f"{dlurl}"),
                    ],
                    [InlineKeyboardButton(text="❰𝗖𝗹𝗼𝘀𝗲❱", callback_data="cls")],
                ]
            )
            requested_by = message.from_user.first_name
            await generate_cover(requested_by, title, views, duration, thumbnail)
            file_path = await convert(youtube.download(url))   
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f" 𝗬𝗼𝘂𝗿 𝗿𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝘀𝗼𝗻𝗴 🎵 **queued** 𝙖𝙩 𝙥𝙤𝙨𝙞𝙩𝙞𝙤𝙣 ☺️ {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file_path)
        except:
            message.reply("Group Call is not connected or I can't join it")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="▶️ 𝙋𝙡𝙖𝙮𝙞𝙣𝙜 𝙝𝙚𝙧𝙚 ☺️ 𝙩𝙝𝙚 𝙨𝙤𝙣𝙜 🎵 𝙧𝙚𝙦𝙪𝙚𝙨𝙩𝙚𝙙 𝙗𝙮 **{}** 𝙫𝙞𝙖 𝙔𝙤𝙪𝙩𝙪𝙗𝙚 𝙈𝙪𝙨𝙞𝙘 📺".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()


@Client.on_message(filters.command("ytplay") & filters.group & ~filters.edited)
async def ytplay(_, message: Message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔄 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜...")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Remember to add helper to your channel</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Add me as admin of yor group first</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "Ⓘ ⓙⓞⓘⓝⓔⓓ ⓣⓗⓘⓢ ⓖⓡⓞⓤⓟ ⓕⓞⓡ ⓟⓛⓐⓨⓘⓝⓖ ⓜⓤⓢⓘⓒ ⓘⓝ ⓋⒸ"
                    )
                    await lel.edit(
                        "ʜᴇʟᴘᴇʀ ᴜꜱᴇʀʙᴏᴛ ᴊᴏɪɴᴇᴅ ʏᴏᴜʀ ᴄʜᴀᴛ",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} couldn't join your group due to heavy requests for userbot! Make sure user is not banned in group."
                        "\n\nOr manually add assistant to your Group and try again</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot not in this chat, Ask admin to send /play command for first time or add {user.first_name} manually</i>"
        )
        return
    await lel.edit("🔎 𝙁𝙞𝙣𝙙𝙞𝙣𝙜")
    user_id = message.from_user.id
    user_name = message.from_user.first_name
     

    query = ""
    for i in message.command[1:]:
        query += " " + str(i)
    print(query)
    await lel.edit("🎵 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜")
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{results[0]['url_suffix']}"
        # print(results)
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        results[0]["url_suffix"]
        views = results[0]["views"]

    except Exception as e:
        await lel.edit(
            "𝐒𝐨𝐧𝐠 🥀 𝐍𝐨𝐭 😔 𝐅𝐨𝐮𝐧𝐝"
        )
        print(str(e))
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", callback_data="playlist"),
                InlineKeyboardButton("❰𝗠𝗲𝗻𝘂 ⏯❱", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(text="❰𝗬𝗼𝘂𝘁𝘂𝗯𝗲❱", url=f"{url}"),
                InlineKeyboardButton(text="❰𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱❱", url=f"{dlurl}"),
            ],
            [InlineKeyboardButton(text="❰𝗖𝗹𝗼𝘀𝗲❱", callback_data="cls")],
        ]
    )
    requested_by = message.from_user.first_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"𝗬𝗼𝘂𝗿 𝗿𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝘀𝗼𝗻𝗴 🎵  **queued**  𝙖𝙩 𝙥𝙤𝙨𝙞𝙩𝙞𝙤𝙣 ☺️ {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
           await callsmusic.set_stream(chat_id, file_path)
        except:
            message.reply("𝐆𝐫𝐨𝐮𝐩 𝐂𝐚𝐥𝐥 𝐢𝐬 𝐧𝐨𝐭 𝐜𝐨𝐧𝐧𝐞𝐜𝐭𝐞𝐝 𝐨𝐫 𝐈 𝐜𝐚𝐧'𝐭 𝐣𝐨𝐢𝐧 𝐢𝐭")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="▶️ 𝙋𝙡𝙖𝙮𝙞𝙣𝙜 𝙝𝙚𝙧𝙚 ☺️ 𝙩𝙝𝙚 𝙨𝙤𝙣𝙜 🎵 𝙧𝙚𝙦𝙪𝙚𝙨𝙩𝙚𝙙 𝙗𝙮  **{}** 𝙫𝙞𝙖 𝙔𝙤𝙪𝙩𝙪𝙗𝙚 𝙈𝙪𝙨𝙞𝙘 📺".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()
    
@Client.on_message(filters.command("dplay") & filters.group & ~filters.edited)
async def deezer(client: Client, message_: Message):
    if message_.chat.id in DISABLED_GROUPS:
        return
    global que
    lel = await message_.reply("🎵 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "DaisyMusic"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Remember to add helper to your channel</b>",
                    )
                    pass
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Add me as admin of yor group first</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "I joined this group for playing music in VC"
                    )
                    await lel.edit(
                        "<b>helper userbot joined your chat</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} couldn't join your group due to heavy requests for userbot! Make sure user is not banned in group."
                        "\n\nOr manually add assistant to your Group and try again</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot not in this chat, Ask admin to send /play command for first time or add {user.first_name} manually</i>"
        )
        return
    requested_by = message_.from_user.first_name

    text = message_.text.split(" ", 1)
    queryy = text[1]
    query = queryy
    res = lel
    await res.edit(f"Searching 👀👀👀 for `{queryy}` on deezer")
    try:
        songs = await arq.deezer(query,1)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        title = songs.result[0].title
        url = songs.result[0].url
        artist = songs.result[0].artist
        duration = songs.result[0].duration
        thumbnail = "https://toppng.com/uploads/preview/and-blank-effect-transparent-11546868080xgtiz6hxid.png"

    except:
        await res.edit("🌸𝗦𝗼𝗻𝗴 𝗡𝗼𝘁 𝗙𝗼𝘂𝗻𝗱 ✌ 𝗦𝗽𝗲𝗹𝗹𝗶𝗻𝗴 𝗣𝗿𝗼𝗯𝗹𝗲𝗺")
        return
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"Music longer than {DURATION_LIMIT}min are not allowed to play")
            return
    except:
        pass    
    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", callback_data="playlist"),
                InlineKeyboardButton("❰𝗠𝗲𝗻𝘂 ⏯❱", callback_data="menu"),
            ],
            [InlineKeyboardButton(text="❰𝗟𝗶𝘀𝘁𝗲𝗻 𝗼𝗻 𝗱𝗲𝗲𝘇𝗲𝗿❱", url=f"{url}")],
            [InlineKeyboardButton(text="❰𝗖𝗹𝗼𝘀𝗲❱", callback_data="cls")],
        ]
    )
    file_path = await convert(wget.download(url))
    await res.edit("Generating Thumbnail")
    await generate_cover(requested_by, title, artist, duration, thumbnail)
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.active_chats:
        await res.edit("adding in queue")
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.edit_text(f"✯{bn}✯= #️⃣ 𝙖𝙩 𝙥𝙤𝙨𝙞𝙩𝙞𝙤𝙣 ☺️ {position}")
    else:
        await res.edit_text(f"✯{bn}✯=▶️ 𝙋𝙡𝙖𝙮𝙞𝙣𝙜.....")

        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file_path)
        except:
            res.edit("Group call is not connected of I can't join it")
            return

    await res.delete()

    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"Playing [{title}]({url}) Via Deezer",
    )
    os.remove("final.png")


@Client.on_message(filters.command("splay") & filters.group & ~filters.edited)
async def jiosaavn(client: Client, message_: Message):
    global que
    if message_.chat.id in DISABLED_GROUPS:
        return    
    lel = await message_.reply("🎵 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝗦𝗼𝘂𝗻𝗱 🔊")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "EzilaXMusic"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Remember to add helper to your channel</b>",
                    )
                    pass
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Add me as admin of yor group first</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "I joined this group for playing music in VC"
                    )
                    await lel.edit(
                        "<b>helper userbot joined your chat</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} couldn't join your group due to heavy requests for userbot! Make sure user is not banned in group."
                        "\n\nOr manually add @MusicHelper to your Group and try again</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            "<i> helper Userbot not in this chat, Ask admin to send /play command for first time or add assistant manually</i>"
        )
        return
    requested_by = message_.from_user.first_name
    chat_id = message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel
    await res.edit(f"🔍 𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐟𝐨𝐫 `{query}` 𝐨𝐧 𝐣𝐢𝐨 𝐬𝐚𝐚𝐯𝐧 🎧")
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        sthumb = songs.result[0].image
        sduration = int(songs.result[0].duration)
    except Exception as e:
        await res.edit("𝐒𝐨𝐧𝐠 🥀 𝐍𝐨𝐭 😔 𝐅𝐨𝐮𝐧𝐝")
        print(str(e))
        return
    try:    
        duuration= round(sduration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"❌ 𝗩𝗶𝗱𝗲𝗼𝘀 𝗹𝗼𝗻𝗴𝗲𝗿 𝘁𝗵𝗮𝗻 {DURATION_LIMIT} 𝗺𝗶𝗻𝘂𝘁𝗲(𝘀) 𝗮𝗿𝗲𝗻'𝘁 𝗮𝗹𝗹𝗼𝘄𝗲𝗱 𝘁𝗼 𝗽𝗹𝗮𝘆!")
            return
    except:
        pass    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", callback_data="playlist"),
                InlineKeyboardButton("❰𝗠𝗲𝗻𝘂 ⏯❱", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(
                    text="Join Updates Channel", url=f"https://t.me/{updateschannel}"
                )
            ],
            [InlineKeyboardButton(text="❰𝗖𝗹𝗼𝘀𝗲❱", callback_data="cls")],
        ]
    )
    file_path = await convert(wget.download(slink))
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.delete()
        m = await client.send_photo(
            chat_id=message_.chat.id,
            reply_markup=keyboard,
            photo="final.png",
            caption=f"✯{bn}✯=#️⃣ Queued at position {position}",
        )

    else:
        await res.edit_text(f"{bn}=▶️ 𝗣𝗹𝗮𝘆𝗶𝗻𝗴.....")
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file_path)
        except:
            res.edit("Group call is not connected of I can't join it")
            return
    await res.edit("Generating Thumbnail.")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"Playing {sname} Via Jiosaavn",
    )
    os.remove("final.png")


@Client.on_callback_query(filters.regex(pattern=r"plll"))
async def lol_cb(b, cb):
    global que

    cbd = cb.data.strip()
    chat_id = cb.message.chat.id
    typed_=cbd.split(None, 1)[1]
    #useer_id = cb.message.reply_to_message.from_user.id
    try:
        x,query,useer_id = typed_.split("|")      
    except:
        await cb.message.edit("Song Not Found")
        return
    useer_id = int(useer_id)
    if cb.from_user.id != useer_id:
        await cb.answer("You ain't the person who requested to play the song!", show_alert=True)
        return
    await cb.message.edit("𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭 🌀... 𝐏𝐥𝐚𝐲𝐞𝐫 𝐬𝐭𝐚𝐫𝐭𝐢𝐧𝐠 📺...")
    x=int(x)
    try:
        useer_name = cb.message.reply_to_message.from_user.first_name
    except:
        useer_name = cb.message.from_user.first_name
    
    results = YoutubeSearch(query, max_results=5).to_dict()
    resultss=results[x]["url_suffix"]
    title=results[x]["title"][:40]
    thumbnail=results[x]["thumbnails"][0]
    duration=results[x]["duration"]
    views=results[x]["views"]
    url = f"https://youtube.com{resultss}"
    
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"❌ 𝗩𝗶𝗱𝗲𝗼𝘀 𝗹𝗼𝗻𝗴𝗲𝗿 𝘁𝗵𝗮𝗻 {DURATION_LIMIT} 𝗺𝗶𝗻𝘂𝘁𝗲(𝘀) 𝗮𝗿𝗲𝗻'𝘁 𝗮𝗹𝗹𝗼𝘄𝗲𝗱 𝘁𝗼 𝗽𝗹𝗮𝘆!")
            return
    except:
        pass
    try:
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
    except Exception as e:
        print(e)
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❰𝗣𝗹𝗮𝘆𝗹𝗶𝘀𝘁❱", callback_data="playlist"),
                InlineKeyboardButton("❰𝗠𝗲𝗻𝘂 ⏯❱", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(text="❰𝗬𝗼𝘂𝘁𝘂𝗯𝗲❱", url=f"{url}"),
                InlineKeyboardButton(text="❰𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱❱", url=f"{dlurl}"),
            ],
            [InlineKeyboardButton(text="❰𝗖𝗹𝗼𝘀𝗲❱", callback_data="cls")],
        ]
    )
    requested_by = useer_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))  
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            caption=f"#⃣ 𝐒𝐨𝐧𝐠 𝐫𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 {r_by.mention} **queued** 𝐀𝐭 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧 {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        
    else:
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
    
        await callsmusic.set_stream(chat_id, file_path)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            reply_markup=keyboard,
            caption=f"▶️ 𝙋𝙡𝙖𝙮𝙞𝙣𝙜 𝙝𝙚𝙧𝙚 ☺️ 𝙩𝙝𝙚 𝙨𝙤𝙣𝙜 🎵 𝙧𝙚𝙦𝙪𝙚𝙨𝙩𝙚𝙙 𝙗𝙮 {r_by.mention} 𝙫𝙞𝙖 𝙔𝙤𝙪𝙩𝙪𝙗𝙚 𝙈𝙪𝙨𝙞𝙘 📺 😎",
        )
        
        os.remove("final.png")
