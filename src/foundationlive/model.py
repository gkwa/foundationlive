import datetime
import typing

import dateutil.parser
import pydantic

now = datetime.datetime.now()
local_now = now.astimezone()
local_tz = local_now.tzinfo


class Invoice(pydantic.BaseModel):
    number: int
    submitted_on: typing.Optional[datetime.datetime] = None
    paid_on: typing.Optional[datetime.datetime] = None

    @pydantic.validator("submitted_on", pre=True, allow_reuse=True)
    @pydantic.validator("paid_on", pre=True, allow_reuse=True)
    def parse_date_as_datetime_obj(cls, v):
        if not v:
            return None

        dt = dateutil.parser.parse(v).replace(tzinfo=local_tz)
        return dt


class InvoiceList(pydantic.BaseModel):
    __root__: typing.List[Invoice]


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


class Timesheet(pydantic.BaseModel):
    invoices: InvoiceList
    days: typing.List[DailyEntry]
