# -*- coding: utf-8 -*-
import asyncio
import os

import botpy
from botpy import logging, BotAPI
from botpy.message import Message, DirectMessage
from botpy.ext.command_util import Commands

QQBOT_APPID = os.getenv("QQBOT_APPID")
QQBOT_TOKEN = os.getenv("QQBOT_TOKEN")

class CHANNEL_ID:
    GPT = '633607434'
    UNIVERSAL = '633601073'


if QQBOT_APPID is None or QQBOT_TOKEN is None:
    raise ValueError("QQBOT_APPID, QQBOT_TOKEN, OPENAI_API_KEY 不能为空")

_log = logging.get_logger()


@Commands(name="help")
async def help_command(api: BotAPI, message, params=None):
    _log.info(params)
    # 第一种用reply发送消息
    help_doc = """你好，我是机器人GPT_Bot-测试中，我会以下命令：
/help: 显示本帮助
/reset: (仅限私信与 ChatGPT Conversation 子频道) 重置 ChatGPT 对话
TODO
"""
    await message.reply(content=help_doc)
    return True


@Commands(name="reset")
async def help_command(api: BotAPI, message, params=None):
    _log.info(params)
    if isinstance(message, DirectMessage):
        reply_content = "重置成功"
    elif isinstance(message, Message):
        if message.channel_id == CHANNEL_ID.GPT:
            reply_content = "重置成功"
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
            help_command
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
                reply_content = f"该频道为 ChatGPT 聊天专属频道，拟用于与 ChatGPT 的分用户对话。"
            case _:
                reply_content = f"错误: 未指定的子频道ID {message.channel_id}"
        await message.reply(content=reply_content)

    async def on_direct_message_create(self, message: DirectMessage):
        handlers = [
            help_command
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
