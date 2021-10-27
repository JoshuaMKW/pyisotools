import time
import webbrowser
from distutils.version import LooseVersion
from logging import StreamHandler
from typing import Iterable, List, Optional

from github import Github
from github.GitRelease import GitRelease
from PySide2.QtCore import Signal

try:
    from .. import __version__
    from .flagthread import FlagThread
except ImportError:
    from pyisotools import __version__
    from pyisotools.gui.flagthread import FlagThread


class ReleaseManager():
    def __init__(self, owner: str, repository: StreamHandler):
        self._owner = owner
        self._repo = repository
        self._releases: List[GitRelease] = list()
        self.populate()

    @property
    def owner(self):
        return self._owner

    @property
    def repository(self):
        return self._repo

    @owner.setter
    def owner(self, owner: str):
        self._owner = owner

    @repository.setter
    def repository(self, repo: str):
        self._repo = repo

    @property
    def releaseLatestURL(self) -> str:
        return f"https://github.com/{self._owner}/{self._repo}/releases/latest"

    @property
    def releasesURL(self) -> str:
        return f"https://github.com/{self._owner}/{self._repo}/releases"

    def get_newest_release(self) -> GitRelease:
        return self._releases[0]

    def get_oldest_release(self) -> GitRelease:
        return self._releases[-1]

    def iter_releases(self) -> Iterable[GitRelease]:
        for v in self._releases:
            yield v

    def compile_changelog_from(self, version: str) -> str:
        """ Returns a Markdown changelog from the info of future versions """
        seperator = "\n\n---\n\n"

        newReleases: List[GitRelease] = list()
        lver = LooseVersion(version.lstrip("v"))
        for release in self.iter_releases():
            if LooseVersion(release.tag_name.lstrip("v")) <= lver:
                break
            newReleases.append(release)

        markdown = ""
        for release in newReleases:
            markdown += release.body.replace("Changelog",
                                             f"Changelog ({release.tag_name})").strip() + seperator

        return markdown.rstrip(seperator).strip()

    def populate(self) -> bool:
        g = Github()
        repo = g.get_repo(f"{self.owner}/{self.repository}")
        self._releases = repo.get_releases()
        return True

    def view(self, release: GitRelease, browser: Optional[webbrowser.GenericBrowser] = None, asWindow: bool = False):
        if browser is None:
            webbrowser.open(release.html_url, int(asWindow))
        else:
            browser.open(release.html_url, int(asWindow))


class GitUpdateScraper(FlagThread, ReleaseManager):

    updateFound = Signal()

    def __init__(self, owner: str, repository: str, parent=None):
        super(FlagThread, self).__init__(parent)
        ReleaseManager.__init__(self, owner, repository)
        self.setObjectName(f"{self.__class__.__name__}.{owner}.{repository}")

        self.waitTime = 0.0

    def set_wait_time(self, seconds: float):
        self.waitTime = seconds

    def run(self):
        while not self.isQuitting():
            successful = self.populate()
            if successful and LooseVersion(self.get_newest_release().tag_name.lstrip("v")) > LooseVersion(__version__.lstrip("v")):
                self.updateFound.emit()

            start = time.time()
            while time.time() - start < self.waitTime and not self.isQuitting():
                time.sleep(1)

    def kill(self):
        self.quit()


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        f"pyisotools v{__version__}", description="ISO tool for extracting/building Gamecube ISOs", allow_abbrev=False)

    parser.add_argument("owner")
    parser.add_argument("repository")

    args = parser.parse_args()

    updater = GitUpdateScraper(args.owner, args.repository)
    release = updater.get_newest_release()
    print(release)
