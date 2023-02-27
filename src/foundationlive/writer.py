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


class ConsoleWriter(Writer):
    def write(self, output: str):
        print(output)
