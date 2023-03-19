import logging
import pathlib

import simple_term_menu

from . import config as configmod

_logger = logging.getLogger(__name__)

base_dir = pathlib.Path(
    configmod.config["FOUNDATIONLIVE_TEMPLATES_OUTPUT_DIRECTORY"]
).expanduser()

_logger.debug(f"{base_dir=}")

lst = [
    "view_csv.txt",
    "view_hours_per_task.txt",
    "view_hours_worked_per_day.txt",
    "view_hours_worked_per_day_summary.txt",
    "view_invoices.txt",
]


def main():

    for file in lst:
        path = base_dir / file
        _logger.debug(f"{path=}")

        if not path.exists():
            lst.remove(path)

    options = lst
    terminal_menu = simple_term_menu.TerminalMenu(options)
    menu_entry_index = terminal_menu.show()
    _logger.debug(f"{menu_entry_index=}")

    if menu_entry_index is not None:
        selected = base_dir / options[menu_entry_index]
        _logger.debug(f"{selected=}")
        print(selected.read_text())


if __name__ == "__main__":
    main()
