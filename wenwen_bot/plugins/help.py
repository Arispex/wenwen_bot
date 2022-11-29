from nonebot import on_command, get_bot
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Message,
    GroupMessageEvent,
    Bot,
)
import config
import models


help = on_command("帮助")


@help.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    await help.finish("指令：\n"
                      "/添加日程 <标题> <内容> <日期>\n"
                      "/查看日程\n"
                      "/查看日程 <ID>\n"
                      "/删除日程 <ID>\n"
                      "/失效日程")
