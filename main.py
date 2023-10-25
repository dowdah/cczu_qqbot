# -*- coding: utf-8 -*-
import asyncio
import os
import json

import botpy
import gpt
from botpy import logging, BotAPI
from botpy.message import Message, DirectMessage
from botpy.ext.command_util import Commands

QQBOT_APPID = os.getenv("QQBOT_APPID")
QQBOT_TOKEN = os.getenv("QQBOT_TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class CHANNEL_ID:
    GPT = '633607434'
    UNIVERSAL = '633601073'


if QQBOT_APPID is None or QQBOT_TOKEN is None:
    raise ValueError("QQBOT_APPID, QQBOT_TOKEN, OPENAI_API_KEY 不能为空")

_log = logging.get_logger()


def load_msg(user_id):
    with open(f"{BASE_DIR}/gpt_msgs.json", "r") as f:
        gpt_msgs = json.load(f)
    if user_id not in gpt_msgs.keys():
        return []
    else:
        return gpt_msgs[user_id]["msgs"]


def save_msg(user_id, msg):
    with open(f"{BASE_DIR}/gpt_msgs.json", "r") as f:
        gpt_msgs = json.load(f)
    if user_id not in gpt_msgs.keys():
        gpt_msgs[user_id] = {}
    gpt_msgs[user_id]["msgs"] = msg
    with open(f"{BASE_DIR}/gpt_msgs.json", "w") as f:
        json.dump(gpt_msgs, f, ensure_ascii=False)


def reset_msg(user_id):
    with open(f"{BASE_DIR}/gpt_msgs.json", "r") as f:
        gpt_msgs = json.load(f)
    if user_id not in gpt_msgs.keys():
        return
    else:
        gpt_msgs[user_id]["msgs"] = []
    with open(f"{BASE_DIR}/gpt_msgs.json", "w") as f:
        json.dump(gpt_msgs, f, ensure_ascii=False)


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
        if message.channel_id == CHANNEL_ID.GPT:
            reset_msg(message.author.id)
            reply_content = "重置成功"
        else:
            reply_content = "错误: 该频道不支持该指令"
    await message.reply(content=reply_content)
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
        if message.channel_id == CHANNEL_ID.GPT:
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


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_at_message_create(self, message: Message):
        _log.info(message.author.avatar)
        _log.info(message.author.username)
        handlers = [
            help_command,
            reset_command,
            say_command
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
