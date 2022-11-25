from tortoise.models import Model
from tortoise import fields


class Schedule(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    time = fields.CharField(max_length=255)
    content = fields.CharField(max_length=255)

    class Meta:
        table = "schedule"

    def __str__(self):
        return self.name
