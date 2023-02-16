import json
import pathlib
import typing

import durations
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


records_path = pathlib.Path("out.json")

with open(records_path) as fh:
    external_data = json.load(fh)

timesheet = Timesheet(**external_data)

# for entry in timesheet.days:
#     for task in entry.tasks.__root__:
#         duration = durations.Duration(task.task_time)
#         seconds = duration.to_seconds()
#         p1 = '${0:.2f}'.format(seconds/60/60*40.87)
#         print(p1, task.task)

task_names = {}
for entry in timesheet.days:
    for task in entry.tasks.__root__:
        task_names.setdefault(task.task, 0)
        duration = durations.Duration(task.task_time)
        task_names[task.task] += duration.to_seconds()

task_names = sorted(task_names.items(), key=lambda x: x[1])
converted_dict = dict(task_names)
# print(converted_dict)

for task, seconds in converted_dict.items():
    r = seconds / 60 / 60 * 4087 / 100
    p1 = "{:6.2f}".format(r)
    print(p1, task)
