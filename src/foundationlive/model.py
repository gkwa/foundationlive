import datetime
import typing

import dateutil.parser
import pydantic
import pydantic.dataclasses


class Task(pydantic.BaseModel):
    task: str
    task_time: str


class TaskList(pydantic.BaseModel):
    __root__: typing.List[Task]


class DailyEntry(pydantic.BaseModel):
    tasks: TaskList
    date: datetime.datetime
    invoice: int
    total_time_sec: typing.Optional[int] = None

    @pydantic.validator("date", pre=True)
    def parse_date_as_datetime_obj(cls, v):
        dt = dateutil.parser.parse(v)
        return dt

    @pydantic.validator("total_time_sec")
    def prevent_none(cls, v):
        assert v is not None, "total_time_sec may not be None"
        return v

    @pydantic.dataclasses.dataclass
    def __post_init__(self):
        self.total_time_sec = [task.task_time for task in self.tasks]


class Timesheet(pydantic.BaseModel):
    days: typing.List[DailyEntry]
