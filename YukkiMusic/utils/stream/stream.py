#
# Copyright (C) 2021-2022 by TeamYukki@Github, < https://github.com/TeamYukki >.
#
# This file is part of < https://github.com/TeamYukki/YukkiMusicBot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TeamYukki/YukkiMusicBot/blob/master/LICENSE >
#
# All rights reserved.

import os
import re
import asyncio
import random
import textwrap
from random import randint
from typing import Union

import aiofiles
import aiohttp

from PIL import (Image, ImageDraw, ImageEnhance, ImageFilter,
                 ImageFont, ImageOps)

from pyrogram.types import InlineKeyboardMarkup
from pyrogram.errors import FloodWait

import config
from config import QUEUE_IMG_URL, YOUTUBE_IMG_URL, MUSIC_BOT_NAME
from YukkiMusic import Carbon, YouTube, app
from YukkiMusic.core.call import Yukki
from YukkiMusic.misc import db
from YukkiMusic.utils.database import (add_active_chat,
                                       add_active_video_chat,
                                       is_active_chat,
                                       is_video_allowed, music_on)
from YukkiMusic.utils.exceptions import AssistantErr
from YukkiMusic.utils.inline.play import (stream_markup,
                                          telegram_markup)
from YukkiMusic.utils.inline.playlist import close_markup
from YukkiMusic.utils.pastebin import Yukkibin
from YukkiMusic.utils.stream.queue import put_queue, put_queue_index
from YukkiMusic.utils.thumbnails import gen_thumb

from youtubesearchpython.__future__ import VideosSearch

STICKERS = [
  "CAACAgQAAxkBAAEJ7AhkzQ7GZ7DrL3O4Q7eHVCAYz-N4nwACvQkAAnpcEVM6alQk5njq3y8E",
  "CAACAgQAAxkBAAEJ7ARkzQ60YZZ7t4ivO7K8VR0LQifh9gACFQwAAtUjEFPkKwhxHG8_Ky8E",
  "CAACAgQAAxkBAAEJ7B1kzRHZ8-XDcyZNUE7Qyc7lsdwFMQACjggAA1VQUdoUwOeQzZqmLwQ",
  "CAACAgQAAxkBAAEJ7AJkzQ6yOkDOwj9r01b7fljN_Boh9wAC6gsAAmwiEVOtWUCotxfPAy8E",
  "CAACAgQAAxkBAAEJ7AABZM0OsGD_J8puJTi9WkLqWQG-SAADuBEAAqbxcR57Dj3-S9mwaS8E",
  "CAACAgQAAxkBAAEJ6_5kzQ6u16es2S8IVUSSQrA9hi_vkwACnxEAAqbxcR57wYUDyflSIS8E",
  "CAACAgEAAxkBAAEJ6_xkzQ50xN3ytZjk5fTylx7DS2PDVgACNgEAAlEpDTkSG_gDZwABw6MvBA",
  "CAACAgEAAxkBAAEJ6_pkzQ5lhNGO3pF1awcVfWxfBC_lQwACGQEAAlEpDTkG9n5mFbHKpy8E",
  "CAACAgEAAxkBAAEJ6_hkzQ5jChDHyCPnrf-xuCQQtouztAACFQEAAlEpDTnRN1QlsQ8qLi8E",
  "CAACAgUAAxkBAAEJ6_ZkzQ3ldTCPnhslPTxQUoirypK47wACowYAAkME2FZILCjifFdIUC8E",
  "CAACAgQAAxkBAAEJ6_BkzQ2qVDgusETUthPZSJ0l4YyKyAACLwoAAgM8IFMao7hilxhkGi8E",
  "CAACAgEAAxkBAAEJ6-5kzQ2UPyvOoBhBh55zDwnpxy2S2QAC8wQAAlEpDTmH9fRvHZACii8E",
  "CAACAgQAAxkBAAEJ6-xkzQ1cU-Oxv0vMWC1Hy-uhlASEAwACpwoAAn-aOFAK54ox7NBRcC8E",
  "CAACAgQAAxkBAAEJ6-pkzQ0mL58wlqP6tTloYWOxYbwFgQACXgwAAghGuVOWomIaBycL7i8E",
  "CAACAgIAAxkBAAEJ66dkzPAnyyPwli7yRX1hpMMQb7PJTgACDQEAAladvQpG_UMdBUTXly8E",
  "CAACAgEAAxkBAAEJ66FkzPARmsJrT_FfgYn1A7BumF3CnwACuwADUSkNOR12rpeAPL_kLwQ",
  "CAACAgEAAxkBAAEJ655kzPANksJJTQXkWl1q1E729tegAgACuAADUSkNOeiAtZ8X-LsKLwQ",
  "CAACAgEAAxkBAAEJ65tkzPAH_xsIpOKY3y6pugABWnGYHdsAArMAA1EpDTkH2Th_5u9jEy8E",
  "CAACAgEAAxkBAAEJ65lkzO_5oUKK3Z5k8JTOjLW62Vr9gwACmgADUSkNOfUGBWVzkcCyLwQ",
  "CAACAgEAAxkBAAEJ65VkzO_yfQABWNWzp75LTIFwfN4PhFsAApMAA1EpDTkdCAmv9TYB9i8E",
  "CAACAgEAAxkBAAEJ65NkzO_qf0xu4BaRSEAEfKmVmYo9EAACjAADUSkNOaEz-mHfkE3aLwQ",
  "CAACAgQAAxkBAAEJ64ZkzO7Je62eg3T6QZNxgvNXMxQYzAACpRYAAqbxcR7qDYebQsdZoi8E",
]

async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return
    if video:
        if not await is_video_allowed(chat_id):
            raise AssistantErr(_["play_7"])
    if forceplay:
        await Yukki.force_stop_stream(chat_id)
    if streamtype == "playlist":
        msg = f"{_['playlist_16']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(
                    search, False if spotify else True
                )
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}- {title[:70]}\n"
                msg += f"{_['playlist_17']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except:
                    raise AssistantErr(_["play_16"])
                await Yukki.join_call(
                    chat_id, original_chat_id, file_path, video=status
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )                
                img = await gen_thumb(vidid, user_id)
                button = stream_markup(_, vidid, chat_id)                
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        user_name,
                        f"https://t.me/{app.username}?start=info_{vidid}",
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
                await asyncio.sleep(1)
                await app.send_sticker(
                    original_chat_id, "CAACAgQAAxkBAAEJ6sFkzJNMUnUYY2GplLCBILGOB2uANQACcQsAAo9SSVFFVmZZbQ1DPi8E" #hearts thooki podura sticker
                    )                
        if count == 0:
            return
        else:
            link = await Yukkibin(msg)
            lines = msg.count("\n")
            if lines >= 17:
                car = os.linesep.join(msg.split(os.linesep)[:17])
            else:
                car = msg
            carbon = await Carbon.generate(
                car, randint(100, 10000000)
            )
            upl = close_markup(_)
            return await app.send_photo(
                original_chat_id,
                photo=carbon,
                caption=_["playlist_18"].format(link, position),
                reply_markup=upl,
            )
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        status = True if video else None
        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, videoid=True, video=status
            )
        except:
            raise AssistantErr(_["play_16"])
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_photo(
                original_chat_id,
                photo=QUEUE_IMG_URL,
                caption=_["queue_4"].format(
                    position, title[:30], duration_min, user_name
                ),
            )            
            #dei = await app.send_sticker(
                #original_chat_id,
                #"CAACAgUAAxkBAAEJ511ky3CVJRVZGvGXdQZ1pNJLbrE9VQACdAYAAiFP4VQEeuQWBclToC8E")
            #await asyncio.sleep(1)
            #await dei.delete()
          
        else:
            if not forceplay:
                db[chat_id] = []
            await Yukki.join_call(
                chat_id, original_chat_id, file_path, video=status
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await gen_thumb(vidid, user_id)
            button = stream_markup(_, vidid, chat_id)            
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    user_name,
                    f"https://t.me/{app.username}?start=info_{vidid}",
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            await asyncio.sleep(1)
            await app.send_sticker(
                original_chat_id, random.choice(STICKERS)  #meditation dance uh.. munnadi hearts thooki podura sticker
                )
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                ),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Yukki.join_call(
                chat_id, original_chat_id, file_path, video=None
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_3"].format(
                    title, duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                ),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Yukki.join_call(
                chat_id, original_chat_id, file_path, video=status
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if video:
                await add_active_video_chat(chat_id)
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL
                if video
                else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_4"].format(
                    title, link, duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await asyncio.sleep(1)
            await app.send_sticker(
                original_chat_id, "CAACAgQAAxkBAAEJ7AZkzQ63doKK_7N7JwbqIJsuacZu8gACoBEAAqbxcR5O5UHja6tzTC8E" #box ulla ukkandhurukum.. munnadi hearts thooki podura sticker
                )
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = "Live Track"
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                ),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            await Yukki.join_call(
                chat_id, original_chat_id, file_path, video=status
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await gen_thumb(vidid, user_id)
            button = telegram_markup(_, chat_id)            
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    user_name,
                    f"https://t.me/{app.username}?start=info_{vidid}",
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await asyncio.sleep(1)
            await app.send_sticker(
                original_chat_id, "CAACAgQAAxkBAAEJ7BVkzRGwd_rAAVxxpkBiS6PrtWr5yQAC7AoAAr8i2VGALarwosnJIi8E" #box ulla ukkandhurukum.. munnadi hearts thooki podura sticker
                )
    elif streamtype == "index":
        link = result
        title = "Index or M3u8 Link"
        duration_min = "URL stream"
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await mystic.edit_text(
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                )
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Yukki.join_call(
                chat_id,
                original_chat_id,
                link,
                video=True if video else None,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
