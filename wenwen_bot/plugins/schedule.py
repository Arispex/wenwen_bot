from nonebot import on_command
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
import datetime

add_schedule = on_command("添加日程", permission=SUPERUSER | models.permission.ADMIN)

remove_schedule = on_command("删除日程", permission=SUPERUSER | models.permission.ADMIN)

check_schedule = on_command("查看日程")


@add_schedule.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if event.group_id in config.groups:
        params = args.extract_plain_text().split(" ")
        # three params: title, time, content
        if len(params) == 4:
            title = params[0]
            time = " ".join(params[2:])
            content = params[1]

            # verify time format(yyyy-mm-dd hh:mm)
            try:
                time_obj = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    time_obj = datetime.datetime.strptime(time, "%m-%d %H:%M")
                except ValueError:
                    await add_schedule.finish("时间格式错误！正确格式：yyyy-mm-dd hh:mm 或 mm-dd hh:mm")

            # Correction time
            if time_obj.year == 1900:
                time_obj = time_obj.replace(year=datetime.datetime.now().year)
                time = time_obj.strftime("%Y-%m-%d %H:%M")

            # verify time is in the future
            if time_obj < datetime.datetime.now():
                await add_schedule.finish("时间不能在过去！")

            # verify title is not empty
            if not title:
                await add_schedule.finish("标题不能为空！")

            # verify content is not empty
            if not content:
                await add_schedule.finish("内容不能为空！")

            # add schedule
            await models.Schedule.create(
                name=title,
                time=time,
                content=content,
            )

            logger.info(f"「{event.get_user_id()}」添加了一个新日程「{title}」")
            await add_schedule.finish("添加成功！")

        else:
            await add_schedule.finish(f"无效的语法！\n正确的语法：/添加日程 <标题> <时间> <内容>")


@remove_schedule.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if event.group_id in config.groups:
        schedule_id = int(args.extract_plain_text())
        if schedule_id:
            schedules = await models.Schedule.get_valid()
            if schedule_id > len(schedules):
                await remove_schedule.finish("日程不存在！")
            else:
                logger.info(f"「{event.get_user_id()}」删除了一个日程「{schedules[schedule_id - 1].name}」")
                await schedules[schedule_id - 1].delete()
                await remove_schedule.finish("删除成功！")
        else:
            await remove_schedule.finish("无效的语法！\n正确的语法：/删除日程 <日程ID>")


@check_schedule.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if event.group_id in config.groups:
        schedule_id = int(args.extract_plain_text())
        if schedule_id:
            schedules = await models.Schedule.get_valid()
            try:
                schedule = schedules[schedule_id - 1]
            except IndexError:
                await check_schedule.finish("日程不存在！")

            await check_schedule.finish(
                f"{schedule.name}\n"
                f"截止时间：{schedule.time}\n"
                f"具体内容：{schedule.content}"
            )
        else:
            await check_schedule.finish("无效的语法！\n正确的语法：/查看日程 <日程ID>")
