import dataclasses
import datetime
import logging
import pathlib
import textwrap

import durations
import jinja2
import pkg_resources
import timeago

from . import model

_logger = logging.getLogger(__name__)

package = __name__.split(".")[0]
templates_dir = pathlib.Path(pkg_resources.resource_filename(package, "templates"))
loader = jinja2.FileSystemLoader(searchpath=templates_dir)
env = jinja2.Environment(loader=loader, keep_trailing_newline=True)

now = datetime.datetime.now()
local_now = now.astimezone()
local_tz = local_now.tzinfo
local_tzname = local_tz.tzname(local_now)
delta_net30 = datetime.timedelta(days=30)


@dataclasses.dataclass
class Thingy:
    fname: str
    fn: str
    data: dict


def view_hours_per_task(timesheet: model.Timesheet):
    names = {}
    for entry in timesheet.days:
        for task in entry.tasks.__root__:
            names.setdefault(task.task, 0)
            duration = durations.Duration(task.task_time)
            names[task.task] += duration.to_seconds()

    by_value = sorted(names.items(), key=lambda kv: kv[1])

    stuff = []
    for task, seconds in by_value:
        delta = datetime.timedelta(seconds=seconds)
        duration = timedelta_to_short_string(delta)
        stuff.append({"duration": duration, "name": task})

    template = env.get_template("view_hours_worked_per_task.j2")
    out = template.render(data=stuff)
    return out


def view_hours_worked_per_day(timesheet: model.Timesheet):
    stuff = []

    for entry in timesheet.days:
        seconds, tasks = 0, []
        for task in entry.tasks.__root__:
            duration = durations.Duration(task.task_time)
            seconds += duration.to_seconds()

            minutia = task.minutia
            minutia = " ".join(minutia.strip().split())
            minutia = textwrap.fill(
                minutia, initial_indent="   ", subsequent_indent="   "
            )

            modified_task = {
                "task": task.task,
                "minutia": minutia,
                "task_time": task.task_time,
            }

            tasks.append(modified_task)

        delta = datetime.timedelta(seconds=seconds)

        x1 = {
            "date": entry.date,
            "worked_time": timedelta_to_short_string(delta),
            "tasks": tasks,
        }
        stuff.append(x1)

    template = env.get_template("view_hours_worked_per_day.j2")
    stuff = sorted(stuff, key=lambda i: i["date"], reverse=True)
    out = template.render(data=stuff)
    return out


def timedelta_to_short_string(td: datetime.timedelta) -> str:
    seconds = td.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    result = ""
    if hours > 0:
        result += f"{int(hours)}h"
    if minutes > 0:
        result += f"{int(minutes)}m"
    if seconds > 0 or not result:
        result += f"{int(seconds)}s"
    return result.strip()


def view_csv(timesheet: model.Timesheet):
    stuff = []
    for entry in timesheet.days:
        for task in entry.tasks.__root__:
            duration = durations.Duration(task.task_time)
            x1 = {
                "task": task.task,
                "date": entry.date,
                "worked_time": duration.to_seconds() / 60 / 60,
                "worked_time_friendly": task.task_time,
                "invoice": entry.invoice,
            }
            stuff.append(x1)

    template = env.get_template("view_csv.j2")

    tasks = sorted(stuff, key=lambda i: i["date"], reverse=True)

    invoice = None
    for task in reversed(tasks):
        if invoice != task["invoice"]:
            invoice = task["invoice"]
            total_per_invoice = 0
        duration = durations.Duration(task["worked_time_friendly"])
        total_per_invoice += duration.to_seconds()
        delta = datetime.timedelta(seconds=total_per_invoice)
        task["worked_time_cumulative"] = timedelta_to_short_string(delta)
        task["worked_time_cumulative_frac"] = total_per_invoice / 3600

    out = template.render(tasks=tasks)
    return out


def view_hours_worked_per_day_summary(timesheet: model.Timesheet):
    daily_entries = []

    total_seconds = 0
    for day in timesheet.days:
        seconds = 0
        for task in day.tasks.__root__:
            seconds += durations.Duration(task.task_time).to_seconds()

        total_seconds += seconds
        delta = datetime.timedelta(seconds=seconds)

        x1 = {
            "date": day.date,
            "worked_duration": delta,
            "invoice_number": day.invoice,
        }
        daily_entries.append(x1)

    template = env.get_template("view_hours_worked_per_day_summary.j2")
    daily_entries = sorted(daily_entries, key=lambda i: i["date"], reverse=True)
    out = template.render(
        data={
            "summary": {"total_seconds_worked": total_seconds},
            "entries": daily_entries,
        }
    )
    return out


def view_invoices(timesheet: model.Timesheet):
    template = env.get_template("view_invoices.j2")
    invoices = timesheet.invoices.__root__

    display_dicts = []
    for invoice in invoices:
        if invoice.submitted_on is None:
            due_date = "N/A"
            due_date_relative = " "
            submitted_on = " "
        else:
            due_date = invoice.submitted_on + delta_net30
            delta = local_now - due_date
            due_date_relative = timeago.format(delta)
            submitted_on = invoice.submitted_on.date()
            ts = invoice.submitted_on + delta_net30
            due_date_relative = f"{due_date_relative} ({ts.strftime('%m-%d')})"

        if invoice.paid_on:
            delta = local_now - invoice.paid_on
            due_date_relative = timeago.format(delta)
            ts = local_now - delta
            due_date_relative = f"{due_date_relative} ({ts.strftime('%m-%d')})"

        display = {
            "submitted": invoice.submitted_on is not None,
            "submitted_on": submitted_on,
            "paid_already": invoice.paid_on is not None,
            "number": invoice.number,
            "due_date_relative": due_date_relative,
        }

        if not invoice.submitted_on:
            display["paid_already"] = " "

        if invoice.paid_on:
            display["paid_already"] = invoice.paid_on.date()

        display_dicts.append(display)

    out = template.render(data=display_dicts)
    return out
