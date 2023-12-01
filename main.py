# -*- coding: utf-8 -*-
import asyncio
import os
import json
import re

import botpy
import gpt
import cczu_spider
from botpy import logging, BotAPI
from botpy.message import Message, DirectMessage
from botpy.ext.command_util import Commands

QQBOT_APPID = os.getenv("QQBOT_APPID")
QQBOT_TOKEN = os.getenv("QQBOT_TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_INFO_FILE = f"{BASE_DIR}/user_info.json"


class Permission:
    ALLOW_GPT = 1
    ALLOW_USERS_COMMAND = 2


class CHANNEL_ID:
    UNIVERSAL = os.getenv("UNIVERSAL_CHANNEL")
    GPT = os.getenv("GPT_CHANNEL")


class Channel:
    def __init__(self, channel_id, name, permissions):
        self.channel_id = channel_id
        self.name = name
        self.permissions = permissions

    def add_permission(self, permission):
        self.permissions |= permission

    def remove_permission(self, permission):
        self.permissions &= ~permission

    def has_permission(self, permission):
        return self.permissions & permission == permission


if QQBOT_APPID is None or QQBOT_TOKEN is None:
    raise ValueError("QQBOT_APPID, QQBOT_TOKEN, OPENAI_API_KEY 不能为空")
with open(f"{BASE_DIR}/channels.json", "r") as f:
    channels = json.load(f)
    channel_dict = dict()
    for channel in channels:
        channel_dict[channel["id"]] = Channel(channel["id"], channel["name"], channel["permissions"])

_log = logging.get_logger()


def load_msg(user_id):
    with open(USER_INFO_FILE, "r") as f:
        user_info = json.load(f)
    if user_id not in user_info.keys():
        return []
    else:
        return user_info[user_id]["msgs"]


def save_msg(user_id, msg):
    with open(USER_INFO_FILE, "r") as f:
        user_info = json.load(f)
    if user_id not in user_info.keys():
        user_info[user_id] = {}
    user_info[user_id]["msgs"] = msg
    with open(USER_INFO_FILE, "w") as f:
        json.dump(user_info, f, ensure_ascii=False)


def reset_msg(user_id):
    with open(USER_INFO_FILE, "r") as f:
        user_info = json.load(f)
    if user_id not in user_info.keys():
        return
    else:
        user_info[user_id]["msgs"] = []
    with open(USER_INFO_FILE, "w") as f:
        json.dump(user_info, f, ensure_ascii=False)


def get_student_id(user_id):
    with open(USER_INFO_FILE, "r") as f:
        user_info = json.load(f)
    if user_id not in user_info.keys():
        return None
    else:
        return user_info[user_id]["student_id"] if user_info[user_id]["student_id"] != "" else None


def set_student_id(user_id, student_id):
    with open(USER_INFO_FILE, "r") as f:
        user_info = json.load(f)
    if user_id not in user_info.keys():
        user_info[user_id] = {}
    user_info[user_id]["student_id"] = student_id
    with open(USER_INFO_FILE, "w") as f:
        json.dump(user_info, f, ensure_ascii=False)


@Commands(name="help")
async def help_command(api: BotAPI, message, params=None):
    _log.info(params)
    # 第一种用reply发送消息
    with open(f"{BASE_DIR}/help_doc", "r") as f:
        help_doc = f.read()
    await message.reply(content=help_doc)
    return True


@Commands(name="reset")
async def reset_command(api: BotAPI, message, params=None):
    _log.info(params)
    if isinstance(message, DirectMessage):
        reset_msg(message.author.id)
        reply_content = "重置成功"
    elif isinstance(message, Message):
        if channel_dict[message.channel_id].has_permission(Permission.ALLOW_GPT):
            reset_msg(message.author.id)
            reply_content = "重置成功"
        else:
            reply_content = "错误: 该频道不支持该指令"
    await message.reply(content=reply_content)
    return True


@Commands(name="users")
async def users_command(api: BotAPI, message, params=None):
    _log.info(params)
    reply_content = "昵称|ID|是否为机器人\n"
    members = await api.get_guild_members(message.guild_id)
    for member in members:
        reply_content += f"{member['user']['username']}|{member['user']['id']}|{'是' if member['user']['bot'] else '否'}\n"
    dms_guild_id = await api.create_dms(guild_id=message.guild_id, user_id=message.author.id)
    dms_guild_id = dms_guild_id['guild_id']
    await api.post_dms(guild_id=dms_guild_id, content=reply_content)
    return True


@Commands(name="say")
async def say_command(api: BotAPI, message, params=None):
    _log.info(params)
    if isinstance(message, DirectMessage):
        reply_content = f"正在与 GPT 进行对话，请稍后..."
        await message.reply(content=reply_content)
        msgs = load_msg(message.author.id)
        msgs.append({'role': 'user', 'content': params})
        reply_content = gpt.chat_with_model(msgs=msgs, user_id=message.author.id)
        msgs.append({'role': 'assistant', 'content': reply_content})
        save_msg(message.author.id, msgs)
    elif isinstance(message, Message):
        if channel_dict[message.channel_id].has_permission(Permission.ALLOW_GPT):
            if params is None:
                reply_content = "错误: 该指令需要参数"
            else:
                reply_content = f"正在与 GPT 进行对话，请稍后..."
                await message.reply(content=reply_content)
                msgs = load_msg(message.author.id)
                msgs.append({'role': 'user', 'content': params})
                reply_content = gpt.chat_with_model(msgs=msgs, user_id=message.author.id)
                msgs.append({'role': 'assistant', 'content': reply_content})
                save_msg(message.author.id, msgs)
        else:
            reply_content = "错误: 该频道不支持该指令"
    await message.reply(content=reply_content)
    return True


@Commands(name="bind")
async def bind_command(api: BotAPI, message, params=None):
    _log.info(params)
    if isinstance(message, DirectMessage):
        reply_content = f"错误: 该指令只能在群组中使用"
    elif isinstance(message, Message):
        if params is None:
            reply_content = "错误: 该指令需要参数"
        elif re.match(r"^\d{10}$", params) is None:
            reply_content = "错误: 该指令的参数必须为10位数字"
        else:
            set_student_id(message.author.id, params)
            reply_content = f"绑定成功，你的学号为 {params}"
    await message.reply(content=reply_content)
    return True


@Commands(name="clockinnum")
async def clockinnum_command(api: BotAPI, message, params=None):
    _log.info(params)
    if isinstance(message, DirectMessage):
        reply_content = f"错误: 该指令只能在群组中使用"
    elif isinstance(message, Message):
        student_id = get_student_id(message.author.id)
        if params:
            reply_content = f"错误: 该指令不需要参数。请使用 /bind 指令绑定你的学号。"
        elif student_id is None:
            reply_content = f"请先使用 /bind 指令绑定你的学号。"
        else:
            reply_content = f"正在与学校查询网站通讯，请等待。(按照历史记录，平均等待时间为31秒)"
            await message.reply(content=reply_content)
            reply_content = cczu_spider.get_pe_clockin_info(get_student_id(message.author.id))
            # if reply_content is None:
            #     reply_content = f"错误: 与学校查询网站通讯失败，请稍后再试。"
    await message.reply(content=reply_content)
    return True


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        _log.info(message.author.avatar)
        _log.info(message.author.username)
        handlers = [
            help_command,
            reset_command,
            say_command,
            users_command,
            bind_command,
            clockinnum_command
        ]
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return
        if "sleep" in message.content:
            await asyncio.sleep(10)
        match message.channel_id:
            case CHANNEL_ID.UNIVERSAL:
                reply_content = f"我是机器人{self.robot.name}\n于{message.timestamp}收到来自{message.channel_id}频道的\
{message.author.username}({message.author.id})的@消息: {message.content}"
            case CHANNEL_ID.GPT:
                reply_content = f"该频道为 GPT 聊天专属频道。你可以使用 /say 指令来与 GPT 进行对话。"
            case _:
                reply_content = f"错误: 未指定的子频道ID {message.channel_id}"
        await message.reply(content=reply_content)

    async def on_direct_message_create(self, message: DirectMessage):
        handlers = [
            help_command,
            reset_command,
            say_command
        ]
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return
        await self.api.post_dms(
            guild_id=message.guild_id,
            content=f"机器人{self.robot.name}收到你的私信了: {message.content}",
            msg_id=message.id,
        )


if __name__ == "__main__":
    # 通过预设置的类型，设置需要监听的事件通道
    # intents = botpy.Intents.none()
    # intents.public_guild_messages=True
    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents.none()
    intents.public_guild_messages = True
    intents.guild_messages = True
    intents.direct_message = True
    client = MyClient(intents=intents)
    client.run(appid=QQBOT_APPID, token=QQBOT_TOKEN)
