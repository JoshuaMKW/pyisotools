import sys
from os import getenv
from pathlib import Path

def resource_path(relative_path: str = "") -> Path:
    """ Get absolute path to resource, works for dev and for cx_freeze """
    if getattr(sys, "frozen", False):
        # The application is frozen
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
        
    return base_path / relative_path

def get_program_folder(folder: str = "") -> Path:
    """ Get path to appdata """
    if sys.platform == "win32":
        datapath = Path(getenv("APPDATA")) / folder
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