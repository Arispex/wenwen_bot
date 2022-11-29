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
import datetime
from nonebot import require
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")

add_schedule = on_command("添加日程", permission=SUPERUSER | models.permission.ADMIN)

remove_schedule = on_command("删除日程", permission=SUPERUSER | models.permission.ADMIN)

check_schedule = on_command("查看日程")

check_invalid_schedules = on_command("失效日程")


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
        schedule_id = args.extract_plain_text()
        if schedule_id:
            schedule_id = int(schedule_id)
            schedules = await models.Schedule.get_valid()
            try:
                schedule = schedules[schedule_id - 1]
            except IndexError:
                await check_schedule.finish("日程不存在！")

            logger.info(f"「{event.get_user_id()}」查看了一个日程「{schedule.name}」")
            await check_schedule.finish(
                f"{schedule.name}\n"
                f"截止时间：{schedule.time}\n"
                f"具体内容：{schedule.content}"
            )
        else:
            schedules = await models.Schedule.get_valid()
            message = []
            schedule_id = 1
            for i in schedules:
                message.append(f"「{schedule_id}」 {i.name} {i.time}")
                schedule_id += 1

            await check_schedule.finish("待完成事项：\n" + "\n".join(message))


@check_invalid_schedules.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if event.group_id in config.groups:
        schedules = await models.Schedule.get_invalid()
        message = []
        num = 1
        for i in schedules:
            message.append(
                f"「{num}」 {i.time} {i.name}"
            )
            num += 1
        logger.info(f"「{event.get_user_id()}」查看了失效日程")
        await check_invalid_schedules.finish("已过期事项：\n" + "\n".join(message))


async def send_valid_schedule():
    bot = get_bot()
    schedules = await models.Schedule.get_valid()
    msg = []
    num = 1
    for i in schedules:
        msg.append(
            f"「{num}」 {i.time} {i.name}"
        )
        num += 1
    logger.info("22点定时任务执行成功！")
    for i in config.groups:
        await bot.send_group_msg(group_id=i, message="待完成事项：\n" + "\n".join(msg))


scheduler.add_job(send_valid_schedule, "cron", hour=22, minute=0, second=0)


async def check_schedule_time():
    # 获取所有日程，分别检测现在是否是每个日程提前12小时和2小时的时间，如果是再判断现在是否处于22点到7点之内
    # 如果不是，就发生提醒
    bot = get_bot()
    schedules = await models.Schedule.get_valid()
    for i in schedules:
        time_obj = datetime.datetime.strptime(i.time, "%Y-%m-%d %H:%M")
        if (datetime.datetime.now() + datetime.timedelta(hours=12)).replace(second=0, microsecond=0) == time_obj:
            if 23 <= datetime.datetime.now().hour or datetime.datetime.now().hour <= 7:
                if (datetime.datetime.now() == 23 and datetime.datetime.now().minute == 0) or (datetime.datetime.now().hour == 6 and datetime.datetime.now().minute == 59):
                    for j in config.groups:
                        logger.info(f"检测到日程「{i.name}」还有12小时就要到期了，发送提醒")
                        await bot.send_group_msg(group_id=j,
                                                 message=f"日程「{i.name}」还有十二个小时就将结束，请检查自己是否完成该日程。")
                else:
                    logger.info(f"检测到日程「{i.name}」还有12小时就要到期了，但是现在是23点到7点之间，不发送提醒")
            else:
                for j in config.groups:
                    logger.info(f"检测到日程「{i.name}」还有12小时就要到期了，发送提醒")
                    await bot.send_group_msg(group_id=j, message=f"日程「{i.name}」还有十二个小时就将结束，请检查自己是否完成该日程。")
        elif (datetime.datetime.now() + datetime.timedelta(hours=2)).replace(second=0, microsecond=0) == time_obj:
            if 23 <= datetime.datetime.now().hour or datetime.datetime.now().hour <= 7:
                if (datetime.datetime.now() == 23 and datetime.datetime.now().minute == 0) or (datetime.datetime.now().hour == 6 and datetime.datetime.now().minute == 59):
                    for j in config.groups:
                        logger.info(f"检测到日程「{i.name}」还有2小时就要到期了，发送提醒")
                        await bot.send_group_msg(group_id=j,
                                                 message=f"日程「{i.name}」还有两个小时就将结束，请检查自己是否完成该日程。")
                else:
                    logger.info(f"检测到日程「{i.name}」还有2小时就要到期了，但是现在是23点到7点之间，不发送提醒")
            else:
                for j in config.groups:
                    logger.info(f"检测到日程「{i.name}」还有2小时就要到期了，发送提醒")
                    await bot.send_group_msg(group_id=j, message=f"日程「{i.name}」还有两个小时就将结束，请检查自己是否完成该日程。")


scheduler.add_job(check_schedule_time, "cron", minute="*/1", second=0)


async def morning_check():
    # 检查每个日程提前12小时和2小时的时间是否处于22点到7点之间，如果是，就发生提醒
    bot = get_bot()
    schedules = await models.Schedule.get_valid()
    for i in schedules:
        time_obj = datetime.datetime.strptime(i.time, "%Y-%m-%d %H:%M")
        if (time_obj - datetime.timedelta(hours=12)).hour > 22:
            for j in config.groups:
                if time_obj.minute == 0:
                    min = ""
                else:
                    min = f"{time_obj.minute}分"
                await bot.send_group_msg(group_id=j,
                                         message=f"日程「{i.name}」将于明早{time_obj.hour}点{min}结束，请检查自己是否完成该日程。")
        elif (time_obj - datetime.timedelta(hours=12)).hour < 7:
            for j in config.groups:
                if time_obj.minute == 0:
                    min = ""
                else:
                    min = f"{time_obj.minute}分"
                await bot.send_group_msg(group_id=j,
                                         message=f"日程「{i.name}」将于明早{time_obj.hour}点{min}结束，请检查自己是否完成该日程。")

        if (time_obj - datetime.timedelta(hours=2)).hour < 7:
            for j in config.groups:
                if time_obj.minute == 0:
                    min = ""
                else:
                    min = f"{time_obj.minute}分"
                await bot.send_group_msg(group_id=j,
                                         message=f"日程「{i.name}」将于明早{time_obj.hour}点{min}结束，请检查自己是否完成该日程。")

        elif (time_obj - datetime.timedelta(hours=2)).hour < 7:
            for j in config.groups:
                if time_obj.minute == 0:
                    min = ""
                else:
                    min = f"{time_obj.minute}分"
                await bot.send_group_msg(group_id=j,
                                         message=f"日程「{i.name}」将于明早{time_obj.hour}点{min}结束，请检查自己是否完成该日程。")


scheduler.add_job(morning_check, "cron", hour=23, minute=0, second=0)