from nonebot import get_plugin_config,get_app,get_bot
from nonebot.plugin import PluginMetadata

from .config import Config

from nonebot import on_message,on_notice
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot,MessageEvent,NoticeEvent,MessageSegment,Message
from nonebot.drivers.fastapi import Request
from .bot import chat_bot
from .util import base64_to_image


__plugin_meta__ = PluginMetadata(
    name="maim-fastapi",
    description="",
    usage="",
    config=Config,
)
    
config = get_plugin_config(Config)

msg_in = on_message(priority=5)
notice_matcher = on_notice(priority=1)

@notice_matcher.handle()
async def _(bot: Bot, event: NoticeEvent):
    logger.debug(f"收到通知：{event}")
    await chat_bot.handle_notice(event, bot)

@msg_in.handle()
async def _(bot: Bot, event: MessageEvent):
    # 处理合并转发消息
    if "forward" in event.message:
        await chat_bot.handle_forward_message(event, bot)
    elif event.reply:
        await chat_bot.handle_reply_message(event,bot)
    elif any(segment.type in {"image", "emoji"} for segment in event.message):  
        await chat_bot.handle_image_message(event, bot)
    else:
        await chat_bot.handle_message(event, bot)

app = get_app()

@app.post("/api/message")
async def handle_request(request: Request):
    try:
        # 接收并解析JSON数据
        json_data = await request.json()
        # logger.info(f"收到请求数据: {json_data}")

        message_info = json_data.get('message_info', {})
        message_segment = json_data.get('message_segment', {})
        group_id = message_info.get('group_info', {}).get('group_id')
        user_id = message_info.get('user_info', {}).get('user_id')

        bot: Bot = get_bot()
        # logger.info("开始处理消息")

        # 初始化消息链和回复ID
        message_chain = Message()
        reply_msg_id = None




        # 处理seglist类型的复合消息
        if message_segment.get('type') == 'seglist':
            for segment in message_segment.get('data', []):
                seg_type = segment.get('type')
                seg_data = segment.get('data')

                if seg_type == 'reply':
                    reply_msg_id = seg_data  # 记录被回复的消息ID
                elif seg_type == 'text':
                    message_chain += MessageSegment.text(seg_data)
                elif seg_type == 'image':
                    image_path = base64_to_image(seg_data)
                    message_chain += MessageSegment.image(file=image_path)
                elif seg_type == 'emoji':
                    # 处理表情消息（示例）
                    # message_chain += MessageSegment.face(id=int(seg_data))
                    image_path = base64_to_image(seg_data)
                    message_chain += MessageSegment.image(file=image_path)
        else:
            # 处理单一类型消息
            seg_type = message_segment.get('type')
            seg_data = message_segment.get('data', '')
            if seg_type == 'text':
                message_chain += MessageSegment.text(seg_data)
            elif seg_type == 'image':
                image_path = base64_to_image(seg_data)
                message_chain += MessageSegment.image(file=image_path)
            elif seg_type == 'emoji':
                image_path = base64_to_image(seg_data)
                message_chain += MessageSegment.image(file=image_path)

        # 添加回复引用（如果存在）
        if reply_msg_id:
            message_chain = MessageSegment.reply(reply_msg_id) + message_chain

        # 发送消息
        if group_id:
            await bot.send_msg(
                message_type="group",
                group_id=group_id,
                message=message_chain
            )
        else:
            await bot.send_msg(
                message_type="private",
                user_id=user_id,
                message=message_chain
            )

        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return {"status": "error", "message": str(e)}


