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

import os
from StreamMusic.config import SOURCE_CODE
from StreamMusic.config import ASSISTANT_NAME
from StreamMusic.config import PROJECT_NAME
from StreamMusic.config import SUPPORT_GROUP
from StreamMusic.config import UPDATES_CHANNEL
class Messages():
      START_MSG = "**Hey,  👋 [{}](tg://user?id={})!**\n\n🤖 I'm ᴀʀᴍʏ Music 🎀 I Cᴀɴ Pʟᴀʏ Mᴜsɪᴄ Iɴ Yᴏᴜʀ Gʀᴏᴜᴩ Vᴏɪᴄᴇ Cʜᴀᴛ..\n\n ☺️ Send me /help for more info."
      HELP_MSG = [
        ".",
f"""
𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗵𝗲𝗹𝗽 𝗽𝗮𝗻𝗻𝗲𝗹 𝗼𝗳 𝗮𝗿𝗺𝘆 𝗺𝘂𝘀𝗶𝗰

🤟𝘼𝙧𝙢𝙮 𝙘𝙖𝙣 𝙥𝙡𝙖𝙮 𝙢𝙪𝙨𝙞𝙘 𝙞𝙣 𝙮𝙤𝙪𝙧 𝙜𝙧𝙤𝙪𝙥'𝙨 𝙫𝙤𝙞𝙘𝙚 𝙘𝙝𝙖𝙩 𝙖𝙨 𝙬𝙚𝙡𝙡 𝙖𝙨 𝙘𝙝𝙖𝙣𝙣𝙚𝙡 𝙫𝙤𝙞𝙘𝙚 𝙘𝙝𝙖𝙩𝙨

🤟𝘼𝙨𝙨𝙞𝙨𝙩𝙖𝙣𝙩 𝙣𝙖𝙢𝙚 >> @{ASSISTANT_NAME}\n\n𝘾𝙡𝙞𝙘𝙠 𝙣𝙚𝙭𝙩 𝙛𝙤𝙧 𝙞𝙣𝙨𝙩𝙧𝙪𝙘𝙩𝙞𝙤𝙣𝙨
""",

f"""
**Setting up**

1) Make bot admin (Group and in channel if use cplay)
2) Start a voice chat
3) Try /play [song name] for the first time by an admin
*) If userbot joined enjoy music, If not add @{ASSISTANT_NAME} to your group and retry

**For Channel Music Play**
1) Make me admin of your channel 
2) Send /userbotjoinchannel in linked group
3) Now send commands in linked group

**Commands**

**=>> Song Playing 🎧**

- /play: Play the requestd song
- /play [yt url] : Play the given yt url
- /play [reply yo audio]: Play replied audio
- /dplay: Play song via deezer
- /splay: Play song via jio saavn
- /ytplay: Directly play song via Youtube Music

**=>> Playback ⏯**

- /player: Open Settings menu of player
- /skip: Skips the current track
- /pause: Pause track
- /resume: Resumes the paused track
- /end: Stops media playback
- /current: Shows the current Playing track
- /playlist: Shows playlist

*Player cmd and all other cmds except /play, /current  and /playlist  are only for admins of the group.
""",
        
f"""
**=>> Channel Music Play 🛠**

⚪️ For linked group admins only:

- /cplay [song name] - play song you requested
- /cdplay [song name] - play song you requested via deezer
- /csplay [song name] - play song you requested via jio saavn
- /cplaylist - Show now playing list
- /cccurrent - Show now playing
- /cplayer - open music player settings panel
- /cpause - pause song play
- /cresume - resume song play
- /cskip - play next song
- /cend - stop music play
- /userbotjoinchannel - invite assistant to your chat

channel is also can be used instead of c ( /cplay = /channelplay )

⚪️ If you donlt like to play in linked group:

1) Get your channel ID.
2) Create a group with tittle: Channel Music: your_channel_id
3) Add bot as Channel admin with full perms
4) Add @{ASSISTANT_NAME} to the channel as an admin.
5) Simply send commands in your group.
""",

f"""
**=>> More tools 🧑‍🔧**

- /musicplayer [on/off]: Enable/Disable Music player
- /admincache: Updates admin info of your group. Try if bot isn't recognize admin
- /userbotjoin: Invite @{ASSISTANT_NAME} Userbot to your chat

**=>> Commands for Sudo Users ⚔️**

 - /userbotleaveall - remove assistant from all chats
 - /gcast <reply to message> - globally brodcast replied message to all chats
 - /pmpermit [on/off] - enable/disable pmpermit message
*Sudo Users can execute any command in any groups

"""
      ]
