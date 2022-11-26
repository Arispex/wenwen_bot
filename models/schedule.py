from pydantic import BaseModel
import models.orm
import datetime


class Schedule(BaseModel):
    id: int
    name: str
    time: str
    content: str

    class Config:
        orm_mode = True

    @classmethod
    async def find(cls, **kwargs):
        return cls.from_orm(await models.orm.Schedule.get(**kwargs))

    @classmethod
    async def create(cls, name: str, time: str, content: str):
        return cls.from_orm(await models.orm.Schedule.create(name=name, time=time, content=content))

    @classmethod
    async def get_all(cls):
        return [cls.from_orm(schedule) for schedule in await models.orm.Schedule.all()]

    @classmethod
    async def get_valid(cls):
        schedules = await models.orm.Schedule.all()
        for i in schedules:
            if datetime.datetime.strptime(i.time, "%Y-%m-%d %H:%M") < datetime.datetime.now():
                schedules.remove(i)

        schedules.sort(key=lambda x: datetime.datetime.strptime(x.time, "%Y-%m-%d %H:%M"))
        return schedules

    async def delete(self):
        await models.orm.Schedule.filter(id=self.id).delete()

    @classmethod
    async def get_invalid(cls):
        schedules = await models.orm.Schedule.all()
        for i in schedules:
            if datetime.datetime.strptime(i.time, "%Y-%m-%d %H:%M") > datetime.datetime.now():
                schedules.remove(i)

        schedules.sort(key=lambda x: datetime.datetime.strptime(x.time, "%Y-%m-%d %H:%M"))
        return schedules