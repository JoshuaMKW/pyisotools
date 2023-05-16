import subprocess
import sys
from os import getenv
from pathlib import Path
from pyisotools import __file__ as _ModulePath


def resource_path(relPath: str = "") -> Path:
    """
    Get absolute path to resource, works for dev and for cx_freeze
    """
    if hasattr(sys, "_MEIPASS"):
        return getattr(sys, "_MEIPASS", Path(__file__).parent) / relPath
    else:
        if getattr(sys, "frozen", False):
            # The application is frozen
            basePath = Path(sys.executable).parent
        else:
            basePath = Path(_ModulePath).parent

        return basePath / relPath


def get_program_folder(folder: str = "") -> Path:
    """
    Get path to appdata
    """
    if sys.platform == "win32":
        appdata = getenv("APPDATA")
        if appdata:
            datapath = Path(appdata) / folder
        else:
            return Path.cwd() / folder
    elif sys.platform == "darwin":
        if folder:
            folder = "." + folder
        datapath = Path("~/Library/Application Support").expanduser() / folder
    elif "linux" in sys.platform:
        if folder:
            folder = "." + folder
        datapath = Path.home() / folder
    else:
        raise NotImplementedError(f"{sys.platform} OS is unsupported")
    return datapath


def open_path_in_explorer(path: Path):
    if sys.platform == "win32":
        subprocess.Popen(
            f"start explorer /select,\"{path.resolve()}\"", shell=True)
    elif sys.platform == "linux":
        subprocess.Popen(["xdg-open", path.resolve()])
    elif sys.platform == "darwin":
        subprocess.Popen(['open', '--', path.resolve()])


def open_path_in_terminal(path: Path):
    if not path.is_dir():
        path = path.parent
    if sys.platform == "win32":
        subprocess.Popen(
            f"start cmd /K cd \"{path.resolve()}\"", shell=True)
    elif sys.platform in {"linux", "darwin"}:
        subprocess.Popen(["gnome-terminal", "-e", f"\"cd {path.resolve}\""])


# bytes pretty-printing
UNITS_MAPPING = (
    (1 << 50, " PB"),
    (1 << 40, " TB"),
    (1 << 30, " GB"),
    (1 << 20, " MB"),
    (1 << 10, " KB"),
    (1, (" byte", " bytes")),
)


# CREDITS: https://stackoverflow.com/a/12912296/13189621
def pretty_filesize(bsize: int, units=UNITS_MAPPING):
    """
    Get human-readable file sizes.
    simplified version of https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in units:
        if bsize >= factor:
            break
    amount = int(bsize / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix
