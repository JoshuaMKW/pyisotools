import re
import sys
import time

from http.client import IncompleteRead

from distutils.version import LooseVersion
from typing import Union
from urllib import request

from bs4 import BeautifulSoup
from PySide2.QtCore import Signal

from .. import __version__
from .flagthread import FlagThread

class ReleaseData(object):
    def __init__(self, version: str = None, info: str = None, downloadLinks: list = None, parentURL: str = None):
        self.version = version
        self.info = info
        self.downloads = downloadLinks
        self.parentURL = parentURL

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<version={self.version}, info={self.info}, downloads={self.downloads}>"


class GitReleaseUpdateScraper(FlagThread):

    updateFound = Signal(ReleaseData)

    def __init__(self, owner: str, repository: str, parent=None):
        super().__init__(parent)
        self._owner = owner
        self._repo = repository
        self.waitCycles = 0
        self.setObjectName(f"{self.__class__.__name__}.{owner}.{repository}")

    def owner(self):
        return self._owner

    def repo(self):
        return self._repo

    def set_owner(self, owner: str):
        self._owner = owner

    def set_repo(self, repo: str):
        self._repo = repo

    @property
    def gitReleasesPageURL(self) -> str:
        return f"https://github.com/{self._owner}/{self._repo}/releases/latest"

    def request_release_data(self, maxTries: int = 10) -> str:
        """ Returns soup data of the repository releases tab """
        responseJSON = b""
        with request.urlopen(self.gitReleasesPageURL) as response:
            for _ in range(maxTries):
                try:
                    responseJSONpart = response.read()
                except IncompleteRead as e:
                    responseJSON += e.partial
                    continue
                else:
                    return responseJSON + responseJSONpart
            return None

    def get_newest_version(self) -> Union[ReleaseData, str]:
        """ Returns newest release version """
        try:
            response = self.request_release_data()
            soup = BeautifulSoup(response, "html.parser")

            version = soup.find("span", {"class": "css-truncate-target"}).get_text(strip=True)
            info = soup.find("div", {"class": "markdown-body"})
            downloads = ["https://github.com" + l.get("href").strip() for l in soup.find_all("a", href=True) if "download" in l.get("href").split("/")]

            releaseInfo = ReleaseData(version, info, downloads, self.gitReleasesPageURL)
            return releaseInfo
        except AttributeError:
            return "No data could be found"
        except request.HTTPError as e:
            return f"HTTP request failed with error code ({e.code})"
        except request.URLError:
            return "Request failed, ensure you have a working internet connection and try again"

    def run(self, period: float = 1.0):
        while True and not self.isQuitting():
            if self.waitCycles <= 0:
                self.waitCycles = 0
                
                info = self.get_newest_version()
                if isinstance(info, ReleaseData) and LooseVersion(info.version.lstrip("v")) > LooseVersion(__version__.lstrip("v")):
                    self.updateFound.emit(info)
            else:
                self.waitCycles -= 1
            
            time.sleep(period)

    def kill(self):
        self.exit(0)

if __name__ == "__main__":
    updater = GitReleaseUpdateScraper("JoshuaMKW", "GeckoLoader")
    state, releaseInfo = updater.get_newest_version()
    print(releaseInfo)
