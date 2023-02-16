import datetime
import pathlib

import durations
import humanize
import jinja2
import pkg_resources

from . import model

package = __name__.split(".")[0]
templates_dir = pathlib.Path(pkg_resources.resource_filename(package, "templates"))
loader = jinja2.FileSystemLoader(searchpath=templates_dir)
env = jinja2.Environment(loader=loader, keep_trailing_newline=True)


def view1(timesheet: model.Timesheet):
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
        age = humanize.naturaldelta(delta)
        stuff.append({"duration": age, "name": task})

    template = env.get_template("view1.j2")
    out = template.render(data=stuff)
    return out


def view2(timesheet: model.Timesheet):
    for entry in timesheet.days:
        for task in entry.tasks.__root__:
            print(entry)
