from PySide2.QtCore import QThread

class FlagThread(QThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._isQuit = False

    def quit(self):
        self._isQuit = True
        super().quit()

    def isQuitting(self):
        return self._isQuit