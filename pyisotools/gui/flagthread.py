from typing import Any, Callable, Tuple
from PySide2.QtCore import QThread

class FlagThread(QThread):
    def __init__(self, target: Callable, args: Tuple[Any] = tuple(), *_args, **_kwargs):
        super().__init__(*_args, **_kwargs)
        self._target = target
        self._args = args
        self._isQuit = False

    def isQuitting(self):
        return self._isQuit

    def quit(self):
        self._isQuit = True
        super().quit()

    def start(self, priority: QThread.Priority = QThread.Priority.NormalPriority):
        self._isQuit = False
        super().start(priority)

    def run(self) -> Any:
        ret = self._target(self._args)
        self._isQuit = True
        return ret