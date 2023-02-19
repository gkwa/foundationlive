import abc
import dataclasses
import pathlib
import stat


class Writer:
    @abc.abstractmethod
    def write(output: str):
        pass


@dataclasses.dataclass
class FileWriter(Writer):
    file: str

    def write(self, output: str):
        path = pathlib.Path(self.file)
        path.write_text(output)
        path.chmod(path.stat().st_mode | stat.S_IEXEC)


@dataclasses.dataclass
class AllInOneWriter(Writer):
    file: str
    path: pathlib.Path = None

    def __post_init__(self):
        self.path = pathlib.Path(self.file)

    def zero(self):
        open(self.path, "w").close()
        return self

    def write(self, output: str):
        with open(self.path, "a") as f:
            f.write(f"{output}\n")
            f.write("-" * 20)
            f.write("\n")


class ConsoleWriter(Writer):
    def write(self, output: str):
        print(output)
