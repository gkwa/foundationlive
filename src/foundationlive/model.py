import typing

import pydantic


class Task(pydantic.BaseModel):
    task: str
    task_time: str


class TaskList(pydantic.BaseModel):
    __root__: typing.List[Task]


class DailyEntry(pydantic.BaseModel):
    tasks: TaskList
    date: str
    invoice: int
    invoice_year: int


class Timesheet(pydantic.BaseModel):
    days: typing.List[DailyEntry]
