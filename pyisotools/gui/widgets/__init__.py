from abc import ABC, ABCMeta

from PySide6.QtWidgets import QWidget


class ABCMetaWidget(type(QWidget), ABCMeta):
    """
    Metaclass designed for QWidgets
    """
    ...


class ABCWidget(ABC, metaclass=ABCMetaWidget):
    """
    Abstract Base Class, for QWidgets
    """
    ...