import json
import os
import sys

from datetime import datetime
from io import BytesIO
from pathlib import Path

from apploader import Apploader
from bi2 import BI2
from bnrparser import BNR
from boot import Boot
from dolreader import DolFile
from fst import FST, FSTNode, FSTRoot
from iohelper import read_uint32

class FileSystemTooLargeError(Exception):
    pass


class ISOBase(FST):

    def __init__(self, root: Path):
        super().__init__(root)
        self.bootheader = None
        self.bootinfo = None
        self.apploader = None
        self.dol = None
        self.fst = None

    def get_fst(self, iso) -> FST:
        iso.seek(0x424)

        _fstloc = read_uint32(iso)
        _fstsize = read_uint32(iso)

        iso.seek(_fstloc)

        self.fst = BytesIO(iso.read(_fstsize))
        return self.load(self.fst)

class WiiISO(ISOBase):

    MaxSize = 4699979776

    def __init__(self, root: Path):
        super().__init__(root)


class GamecubeISO(ISOBase):

    MaxSize = 1459978240

    def __init__(self, root: Path):
        super().__init__(root)
        self.bnr = None

    def build(self, dest: Path, genNewInfo: bool = False):
        def _init_sys(self, genNewInfo: bool):
            systemPath = self.root / "sys"
            self.dol = BytesIO((systemPath / "main.dol").read_bytes())

            with (systemPath / "boot.bin").open("rb") as f:
                self.bootheader = Boot(f)

            with (systemPath / "bi2.bin").open("rb") as f:
                self.bootinfo = BI2(f)

            with (systemPath / "apploader.img").open("rb") as f:
                self.apploader = Apploader(f)

            self.bnr = BNR((self.root / "opening.bnr"))

            with (systemPath / ".config.json").open("r") as f:
                config = json.load(f)

            if genNewInfo:
                self.bnr.gameName = config["name"]
                self.bnr.gameTitle = config["name"]
                self.bootheader.gameName = config["name"]
                self.bootheader.gameCode = config["gameid"][:4]
                self.bootheader.makerCode = config["gameid"][4:6]
                self.bootheader.version = config["version"]
                self.bnr.developerName = config["author"]
                self.bnr.developerTitle = config["author"]
                self.bnr.gameDescription = config["description"]
                self.apploader.buildDate = datetime.today().strftime("%Y/%m/%d") 

            self.bootheader.dolOffset = (0x2440 + self.apploader.trailerSize + 0x1FFF) & -0x2000
            self.bootheader.fstOffset = (self.bootheader.dolOffset + len(self.dol.getbuffer()) + 0x7FF) & -0x800

            self.fst = BytesIO()
            self.rcreate(self.root, self, ignorePath=(self.root / "sys",))
            self.save(self.fst, (self.MaxSize - self.datasize) & -32768)

            self.bootheader.fstSize = len(self.fst.getbuffer())
            self.bootheader.fstMaxSize = self.bootheader.fstSize

            if ((self.bootheader.fstOffset + self.bootheader.fstSize + 0x7FF) & -0x800) + self.datasize > self.MaxSize:
                raise FileSystemTooLargeError(f"{((self.bootheader.fstOffset + self.bootheader.fstSize + 0x7FF) & -0x800) + self.datasize} is larger than the max size of a GCM ({self.MaxSize})")

        _init_sys(self, genNewInfo)

        with dest.open("wb") as ISO:
            self.bootheader.save(ISO)
            self.bootinfo.save(ISO)
            self.apploader.save(ISO)
            ISO.write(b"\x00" * (self.bootheader.dolOffset - ISO.tell()))
            ISO.write(self.dol.getvalue())
            ISO.write(b"\x00" * (self.bootheader.fstOffset - ISO.tell()))
            ISO.write(self.fst.getvalue())
            for child in self.rfiles:
                if child.is_file():
                    ISO.write(b"\x00" * (child._fileoffset - ISO.tell()))
                    ISO.write(child.path.read_bytes())
            ISO.write(b"\x00" * (self.MaxSize - ISO.tell()))

    def extract(self, iso: Path, dest: Path):
        def _init_sys(self, iso):
            iso.seek(0)
            self.bootheader = Boot(iso)
            self.bootinfo = BI2(iso)
            self.apploader = Apploader(iso)
            self.dol = DolFile(iso, self.bootheader.dolOffset)
            self.get_fst(iso)

            bnrNode = self.find_by_path(self.root / "opening.bnr")
            iso.seek(bnrNode._fileoffset)
            self.bnr = BNR(iso)


        systemPath = dest / self.root / "sys"
        dest.mkdir(parents=True, exist_ok=True)
        systemPath.mkdir(parents=True, exist_ok=True)

        with iso.open("rb") as _iso:
            _init_sys(self, _iso)

            prev = FSTNode("fst.bin", FSTNode.FILE, None, self.bootheader.fstSize, self.bootheader.fstOffset)
            for node in self.nodes_by_offset():
                self._alignmentTable[str(node.path).replace(os.sep, '/')] = self._detect_alignment(node, prev)
                prev = node
                
            with (systemPath / "boot.bin").open("wb") as f:
                self.bootheader.save(f)

            with (systemPath / "bi2.bin").open("wb") as f:
                self.bootinfo.save(f)

            with (systemPath / "apploader.img").open("wb") as f:
                self.apploader.save(f)

            with (systemPath / "main.dol").open("wb") as f:
                self.dol.save(f)

            with (systemPath / "fst.bin").open("wb") as f:
                f.write(self.fst.getvalue())

            with (systemPath / ".config.json").open("w") as f:
                config = { "name": self.bootheader.gameName,
                           "gameid": self.bootheader.gameCode + self.bootheader.makerCode,
                           "version": self.bootheader.version,
                           "author": self.bnr.developerTitle,
                           "description": self.bnr.gameDescription,
                           "alignment": self._alignmentTable }
                json.dump(config, f, indent=4)
            
            for root, _, filenodes in self.walk():
                if not root.exists():
                    root.mkdir()
                
                for node in filenodes:
                    (dest / root).mkdir(parents=True, exist_ok=True)
                    with (dest / root / node.name).open("wb") as f:
                        _iso.seek(node._fileoffset)
                        f.write(_iso.read(node.size))

if __name__ == "__main__":
    iso = GamecubeISO(Path("root"))
    #iso.extract(Path("game.iso"), Path().cwd())
    iso.build(Path("test.iso"), genNewInfo=True)