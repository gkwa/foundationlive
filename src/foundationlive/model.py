import datetime
import typing

import dateutil.parser
import pydantic


class Task(pydantic.BaseModel):
    task: str
    task_time: str


class TaskList(pydantic.BaseModel):
    __root__: typing.List[Task]


class DailyEntry(pydantic.BaseModel):
    tasks: TaskList
    date: datetime.datetime
    invoice: int

    @pydantic.validator("date", pre=True)
    def parse_date_as_datetime_obj(cls, v):
        dt = dateutil.parser.parse(v)
        return dt


class Timesheet(pydantic.BaseModel):
    days: typing.List[DailyEntry]
