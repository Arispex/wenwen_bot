from nonebot.adapters import Bot, Event
from nonebot.internal.permission import Permission as Permission
import json


class Admin:
    """
    管理员权限
    """
    async def __call__(self, bot: Bot, event: Event) -> bool:
        try:
            with open("admins.json", "r") as fp:
                admins = json.load(fp)
        except FileNotFoundError:
            admins = []
            with open("admins.json", "w") as fp:
                json.dump(admins, fp)
        return event.get_type() == "message" and event.get_user_id() in admins


ADMIN: Permission = Permission(Admin())
