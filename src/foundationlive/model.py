import datetime
import logging
import typing

import dateutil.parser
import pydantic

_logger = logging.getLogger(__name__)

now = datetime.datetime.now()
local_now = now.astimezone()
local_tz = local_now.tzinfo


def date_str_to_datetime(date: str) -> datetime.datetime:
    if not date:
        return None

    dt = dateutil.parser.parse(date).replace(tzinfo=local_tz)
    return dt


class Invoice(pydantic.BaseModel):
    number: int
    submitted_on: typing.Optional[datetime.datetime] = None
    paid_on: typing.Optional[datetime.datetime] = None

    # validators
    # https://docs.pydantic.dev/usage/validators/#reuse-validators
    _normalize_submitted_on = pydantic.validator(
        "submitted_on", pre=True, allow_reuse=True
    )(date_str_to_datetime)

    _normalize_paid_on = pydantic.validator("paid_on", pre=True, allow_reuse=True)(
        date_str_to_datetime
    )


class InvoiceList(pydantic.BaseModel):
    __root__: typing.List[Invoice]


class Task(pydantic.BaseModel):
    task: str
    minutia: typing.Optional[str] = ""
    task_time: str


class TaskList(pydantic.BaseModel):
    __root__: typing.List[Task]


class DailyEntry(pydantic.BaseModel):
    tasks: TaskList
    date: datetime.datetime
    invoice: int
    total_time_sec: typing.Optional[int] = None

    _normalize_date = pydantic.validator("date", pre=True, allow_reuse=True)(
        date_str_to_datetime
    )

    @pydantic.validator("total_time_sec")
    def prevent_none(cls, v):
        assert v is not None, "total_time_sec may not be None"
        return v


class Timesheet(pydantic.BaseModel):
    invoices: InvoiceList
    days: typing.List[DailyEntry]
