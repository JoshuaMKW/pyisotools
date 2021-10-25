import sys
from pathlib import Path

def resource_path(relPath: str = "") -> Path:
    """ Get absolute path to resource, works for dev and for cx_freeze """
    if hasattr(sys, "_MEIPASS"):
        return getattr(sys, "_MEIPASS", Path(__file__).parent) / relPath
    else:
        if getattr(sys, "frozen", False):
            # The application is frozen
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).parent
            
        return base_path / relPath

def get_program_folder(folder: str = "") -> Path:
    """ Get path to appdata """
    from os import getenv
    
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