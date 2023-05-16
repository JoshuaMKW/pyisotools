from enum import Enum
from typing import Optional
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCursor, QIcon, QImage, QPixmap

from pyisotools.utils.filesystem import resource_path


class CommonCursor(str, Enum):
    COLOR_PICKER = "gui/cursors/color_picker.png"


def get_common_cursor(cursor: CommonCursor, size: QSize = QSize(20, 20)) -> QCursor:
    cursorPix = QPixmap(str(resource_path(cursor.value)))
    cursorScaledPix = cursorPix.scaled(size, Qt.KeepAspectRatio)

    return QCursor(cursorScaledPix, -1, -1)


def get_image(filename: str, size: Optional[QSize] = None) -> QImage | None:
    path = resource_path("gui/icons/" + filename)
    if not path.is_file():
        return None

    image = QImage(str(path))
    if size:
        return image.scaled(size)
    return image


def get_icon(filename: str) -> QIcon | None:
    path = resource_path("gui/icons/" + filename)
    if not path.is_file():
        return None
    return QIcon(str(path))
