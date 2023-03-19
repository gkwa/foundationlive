import calendar
import collections
import copy
import csv
import dataclasses
import datetime
import io
import logging
import pathlib
import textwrap

import durations
import holidays
import inflect
import jinja2
import pkg_resources
import timeago

from . import config as configmod
from . import model

_logger = logging.getLogger(__name__)

package = __name__.split(".")[0]
templates_dir = pathlib.Path(pkg_resources.resource_filename(package, "templates"))
loader = jinja2.FileSystemLoader(searchpath=templates_dir)
env = jinja2.Environment(loader=loader, keep_trailing_newline=True)

sec_per_hour = datetime.timedelta(hours=1).total_seconds()
now = datetime.datetime.now()
local_now = now.astimezone()
local_tz = local_now.tzinfo
local_tzname = local_tz.tzname(local_now)
delta_net30 = datetime.timedelta(days=30)
hourly_rate = float(configmod.config["HOURLY_RATE"]) or 0.0


def get_net30(start_date: datetime.datetime, net30=delta_net30) -> datetime.timedelta:
    """
    Given some date start_date, return the timedelta till the non-holiday monday
    after (start_date + 30 days).
    """
    us_holidays = holidays.US(years=start_date.year)

    def is_holiday_or_weekend(date):
        return date.weekday() >= 5 or date in us_holidays

    next_weekday = start_date + net30
    while is_holiday_or_weekend(next_weekday):
        next_weekday += datetime.timedelta(days=1)

    return next_weekday - start_date


@dataclasses.dataclass
class Thingy:
    fname: str
    fn: str
    data: dict


def view_hours_per_task(timesheet: model.Timesheet) -> str:
    names = {}
    invoices = set()
    for entry in timesheet.days:
        for task in entry.tasks.__root__:
            names.setdefault(task.task, 0)
            duration = durations.Duration(task.task_time)
            names[task.task] += duration.to_seconds()
            invoices.add(entry.invoice)

    by_value = sorted(names.items(), key=lambda kv: kv[1])

    stuff = []
    total_time = datetime.timedelta(seconds=0)
    for task, seconds in by_value:
        delta = datetime.timedelta(seconds=seconds)
        stuff.append(
            {"duration_friendly": timedelta_to_short_string(delta), "name": task}
        )
        total_time += delta

    label_total = f"invoice {str(invoices.pop())} total"
    if len(invoices) > 1:
        label_total = f"invoices {', '.join([str(x) for x in invoices])} total"

    template = env.get_template("view_hours_worked_per_task.j2")
    inv_str = template.render(
        data={
            "invoices": invoices,
            "stuff": stuff,
            "total_time": timedelta_to_short_string(total_time),
            "label_total": label_total,
        }
    )
    return inv_str


def view_hours_worked_per_day(timesheet: model.Timesheet) -> str:
    stuff = []

    for entry in timesheet.days:
        seconds, tasks = 0, []
        for task in entry.tasks.__root__:
            duration = durations.Duration(task.task_time)
            seconds += duration.to_seconds()

            minutia = task.minutia
            minutia = " ".join(minutia.strip().split())
            minutia = textwrap.fill(
                minutia,
                initial_indent=" " * 3,
                subsequent_indent=" " * 3,
                break_long_words=False,
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
    stuff = sorted(stuff, key=lambda i: i["date"], reverse=False)
    return template.render(data=stuff)


def view_hours_worked_per_day_summary(timesheet: model.Timesheet) -> str:
    daily_entries = []

    total_time_worked = datetime.timedelta(seconds=0)

    for day in sorted(timesheet.days, key=lambda i: i.date, reverse=False):
        seconds = 0
        for task in day.tasks.__root__:
            seconds += durations.Duration(task.task_time).to_seconds()

        total_time_worked += datetime.timedelta(seconds=seconds)

        earned = hourly_rate * total_time_worked.total_seconds() / sec_per_hour
        earned = "${:,.2f}".format(earned)
        earned = "{:>10}".format(earned)

        x1 = {
            "date": day.date,
            "worked_duration_friendly": timedelta_to_short_string(total_time_worked),
            "invoice_number": day.invoice,
            "earned": earned,
            "rate_not_zero": hourly_rate != 0.0,
        }
        daily_entries.append(x1)

    template = env.get_template("view_hours_worked_per_day_summary.j2")
    daily_entries = sorted(daily_entries, key=lambda i: i["date"], reverse=True)

    x = total_time_worked.total_seconds() / sec_per_hour
    total_time_worked_friendly = (
        "{:d}h".format(int(x)) if int(x) == x else "{0:.2f}h".format(x)
    )

    view_str = template.render(
        data={
            "summary": {"total_time_worked_friendly": total_time_worked_friendly},
            "entries": daily_entries,
        }
    )
    return view_str


def timedelta_to_short_string(td: datetime.timedelta) -> str:
    seconds = td.total_seconds()
    hours, remainder = divmod(seconds, sec_per_hour)
    minutes, seconds = divmod(remainder, 60)
    result = ""
    if hours > 0:
        result += f"{int(hours)}h"
    if minutes > 0:
        result += f"{int(minutes)}m"
    if seconds > 0 or not result:
        result += f"{int(seconds)}s"
    return result.strip()


def generate_csv_data(timesheet: model.Timesheet) -> list[dict]:
    stuff = []
    for entry in timesheet.days:
        for task in entry.tasks.__root__:
            duration = durations.Duration(task.task_time)

            minutia = task.minutia
            minutia = " ".join(minutia.strip().split())
            minutia = textwrap.fill(minutia, width=999_999_999)

            x1 = {
                "task": task.task,
                "date": entry.date,
                "worked_time": duration.to_seconds() / sec_per_hour,
                "worked_time_friendly": task.task_time,
                "invoice": entry.invoice,
                "minutia": minutia,
            }
            stuff.append(x1)

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
        task["worked_time_cumulative_frac"] = total_per_invoice / sec_per_hour

    return tasks


def view_csv_stringio(tasks: list[dict]) -> io.StringIO:
    tasks = copy.deepcopy(tasks)
    headers = collections.OrderedDict(
        {
            "date": "date",
            "invoice": "invoice",
            "inv total": "worked_time_cumulative",
            "duration": "worked_time_friendly",
            "task": "task_details_pretty",
        }
    )

    data = []
    for task in tasks:
        x1 = task["date"].strftime("%a %m-%d")
        x2 = task["worked_time_friendly"]
        x3 = task["worked_time"]
        x4 = task["worked_time_cumulative"]
        x5 = task["worked_time_cumulative_frac"]

        task["date"] = x1
        task["worked_time_cumulative"] = f"{x4} ({x5:.2f})"
        task["worked_time_friendly"] = f"{x2} ({x3:.2f})"
        task["task_details_pretty"] = (
            f"{task['task']} - {task['minutia']}" if task["minutia"] else task["task"]
        )
        dct = {}
        for header, key in headers.items():
            dct[header] = task[key]

        data.append(dct)

    my_stringio = io.StringIO()
    writer = csv.DictWriter(my_stringio, fieldnames=headers.keys())
    writer.writeheader()
    for row in data:
        writer.writerow(row)

    return my_stringio


def view_csv_jinja2(timesheet: model.Timesheet) -> str:
    tasks = generate_csv_data(timesheet)
    template = env.get_template("view_csv.j2")
    return template.render(tasks=tasks)


def view_google_sheets(timesheet: model.Timesheet) -> str:
    tasks = generate_csv_data(timesheet)
    return view_csv_stringio(tasks).getvalue()


def view_invoices(timesheet: model.Timesheet) -> str:
    template = env.get_template("view_invoices.j2")
    invoices = timesheet.invoices.__root__
    invoices_by_inv_number = sorted(invoices, key=lambda x: x.number, reverse=False)

    today = datetime.datetime.today()

    _, days_in_this_month = calendar.monthrange(today.year, today.month)
    month_last_day = datetime.datetime(today.year, today.month, days_in_this_month)
    month_middle = datetime.datetime(today.year, today.month, 15)
    submittal_due_date = month_middle if today < month_middle else month_last_day

    _logger.debug(f"{submittal_due_date=}")
    _logger.debug(f"{month_middle=}")
    _logger.debug(f"{month_last_day=}")
    _logger.debug(f"{datetime.datetime.now().date()=}")

    if datetime.datetime.now().date() == month_middle.date():
        submittal_due_date = datetime.datetime.now()

    submittal_due_from_now_delta = (
        submittal_due_date - today + datetime.timedelta(days=1)
    )

    if datetime.datetime.now().date() == month_middle.date():
        submittal_due_date = datetime.datetime.now() + submittal_due_from_now_delta

    display_dicts = []
    for invoice in invoices_by_inv_number:
        due_date = "N/A"
        payout_due_relative = " "
        submitted_on = None

        if invoice.submitted_on is not None:
            s = invoice.submitted_on
            due_date = s + get_net30(s, delta_net30)
            delta = due_date - local_now + datetime.timedelta(days=1)
            submitted_on = invoice.submitted_on.date()
            ts = s + get_net30(s, delta_net30)
            days = inflect.engine().plural("day", delta.days)
            date = ts.strftime("%m-%d")
            payout_due_relative = f"in {delta.days} {days} on {date}"

            if delta.days == 0:
                payout_due_relative = "today"

        if invoice.paid_on:
            delta = local_now - invoice.paid_on
            payout_due_relative = timeago.format(delta)

        display = {
            "submitted": invoice.submitted_on is not None,
            "submitted_on": submitted_on,
            "submittal_due_from_now_delta": submittal_due_from_now_delta,
            "submittal_due_date": submittal_due_date,
            "paid_already": invoice.paid_on is not None,
            "number": invoice.number,
            "payout_due_relative": payout_due_relative,
        }

        if not invoice.submitted_on:
            display["paid_already"] = " "

        if invoice.paid_on:
            display["paid_already"] = invoice.paid_on.date()

        display_dicts.append(display)

    return template.render(data=display_dicts)
