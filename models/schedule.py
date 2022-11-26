from pydantic import BaseModel
import models.orm


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