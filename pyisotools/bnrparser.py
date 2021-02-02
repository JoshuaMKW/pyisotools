from __future__ import annotations

import json

from argparse import ArgumentParser
from functools import wraps
from io import BytesIO
from pathlib import Path

from PIL import Image


def _read_string(io, offset: int = 0, maxlen: int = 0, encoding: str = "iso-8859-1") -> str:
    io.seek(offset)
    cString = io.read(maxlen)
    return cString.rstrip(b"\x00").decode(encoding)


def io_preserve(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        _loc = self._rawdata.tell()
        value = func(self, *args, **kwargs)
        self._rawdata.seek(_loc)
        return value
    return wrapper


class Jobs:
    COMPILE = "COMPILE"
    EXTRACT = "EXTRACT"


class RGB5A1(object):

    TileWidth = 4
    TileHeight = 4

    @staticmethod
    def encode_pixel(pixel: tuple) -> int:
        """ RGB888 or RGBA8888 ONLY """
        r = (pixel[0] >> 3) & 0b11111
        g = (pixel[1] >> 3) & 0b11111
        b = (pixel[2] >> 3) & 0b11111

        if len(pixel) == 3:
            a = 1
        else:
            a = 1 if pixel[3] & 0x80 else 0

        return (a << 15) | (r << 10) | (g << 5) | b

    @staticmethod
    def decode_pixel(pixel: int) -> tuple:
        """ RGBA8888 ONLY """
        r = ((pixel >> 10) & 0b11111) << 3
        g = ((pixel >> 5) & 0b11111) << 3
        b = (pixel & 0b11111) << 3
        a = (pixel >> 15) * 0xFF

        return (r, g, b, a)


class BNR(RGB5A1):
    class Regions:
        AMERICA = 0
        EUROPE = 1
        JAPAN = 2
        KOREA = 0

    ImageWidth = 96
    ImageHeight = 32

    ImgTileWidth = ImageWidth // RGB5A1.TileWidth
    ImgTileHeight = ImageHeight // RGB5A1.TileHeight

    def __init__(self, f: Path, region: Regions = Regions.AMERICA, gameName: str = "", gameTitle: str = "", developerName: str = "", developerTitle: str = "", desc: str = "", overwrite=False):
        self._rawdata = BytesIO(b"\x00" * (0x1960 if region != BNR.Regions.EUROPE else 0x1FA0))
        self.regionID = region
        self.index = 0
        
        self.load(f, region, gameName, gameTitle,
                  developerName, developerTitle, desc, overwrite)

    @classmethod
    def from_data(cls, obj, region: Regions = Regions.AMERICA, size: int = -1):
        self = cls.__new__(cls)
        self._rawdata = BytesIO(obj.read(size))
        self.regionID = region
        self.index = 0
        return self

    @property
    def isBNR2(self) -> bool:
        return self.magic == "BNR2" and len(self._rawdata.getbuffer()) == 0x1FA0

    @property
    def region(self) -> str:
        if self.regionID == BNR.Regions.AMERICA:
            return "NTSC-U"
        elif self.regionID == BNR.Regions.EUROPE:
            return "PAL"
        elif self.regionID == BNR.Regions.JAPAN:
            return "NTSC-J"
        else:
            return "NTSC-K"

    @property
    @io_preserve
    def magic(self) -> str:
        self._rawdata.seek(0)
        return self._rawdata.read(4).decode("iso-8859-1")

    @magic.setter
    @io_preserve
    def magic(self, region: Regions):
        self._rawdata.seek(0)

        if region == BNR.Regions.EUROPE and len(self._rawdata.getbuffer()) == 0x1FA0:
            self._rawdata.write(b"BNR2")
        else:
            self._rawdata.write(b"BNR1")

    @property
    @io_preserve
    def rawImage(self) -> BytesIO:
        self._rawdata.seek(0x20)
        return BytesIO(self._rawdata.read(0x1800))

    @rawImage.setter
    @io_preserve
    def rawImage(self, _img: [bytes, BytesIO, Image.Image]):
        self._rawdata.seek(0x20)
        if isinstance(_img, bytes):
            self._rawdata.write(_img[:0x1800])
        elif isinstance(_img, BytesIO):
            self._rawdata.write(_img.getvalue()[:0x1800])
        elif isinstance(_img, Image.Image):
            smallImg = _img.resize((BNR.ImageWidth, BNR.ImageHeight))
            for yBlock in range(BNR.ImgTileHeight):
                for xBlock in range(BNR.ImgTileWidth):
                    for iy in range(BNR.TileHeight):
                        for ix in range(BNR.TileWidth):
                            x = xBlock*BNR.TileWidth + ix
                            y = yBlock*BNR.TileHeight + iy

                            pixel = smallImg.getpixel((x, y))
                            if x < BNR.ImageWidth and y < BNR.ImageHeight:
                                self._rawdata.write(self.encode_pixel(
                                    pixel).to_bytes(2, "big", signed=False))

    @property
    @io_preserve
    def gameName(self) -> str:
        return _read_string(self._rawdata, 0x1820 + (self.index * 0x140), 0x20, encoding="iso-8859-1" if self.region != "NTSC-J" else "shift-jis")

    @gameName.setter
    @io_preserve
    def gameName(self, name: str):
        self._rawdata.seek(0x1820 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x20)
        self._rawdata.seek(0x1820 + (self.index * 0x140))
        self._rawdata.write(bytes(name[:0x1F], "iso-8859-1" if self.region != "NTSC-J" else "shift-jis"))

    @property
    @io_preserve
    def developerName(self) -> str:
        return _read_string(self._rawdata, 0x1840 + (self.index * 0x140), 0x20, encoding="iso-8859-1" if self.region != "NTSC-J" else "shift-jis")

    @developerName.setter
    @io_preserve
    def developerName(self, name: str):
        self._rawdata.seek(0x1840 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x20)
        self._rawdata.seek(0x1840 + (self.index * 0x140))
        self._rawdata.write(bytes(name[:0x1F], "iso-8859-1" if self.region != "NTSC-J" else "shift-jis"))

    @property
    @io_preserve
    def gameTitle(self) -> str:
        return _read_string(self._rawdata, 0x1860 + (self.index * 0x140), 0x40, encoding="iso-8859-1" if self.region != "NTSC-J" else "shift-jis")

    @gameTitle.setter
    @io_preserve
    def gameTitle(self, name: str):
        self._rawdata.seek(0x1860 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x40)
        self._rawdata.seek(0x1860 + (self.index * 0x140))
        self._rawdata.write(bytes(name[:0x3F], "iso-8859-1" if self.region != "NTSC-J" else "shift-jis"))

    @property
    @io_preserve
    def developerTitle(self) -> str:
        return _read_string(self._rawdata, 0x18A0 + (self.index * 0x140), 0x40, encoding="iso-8859-1" if self.region != "NTSC-J" else "shift-jis")

    @developerTitle.setter
    @io_preserve
    def developerTitle(self, name: str):
        self._rawdata.seek(0x18A0 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x40)
        self._rawdata.seek(0x18A0 + (self.index * 0x140))
        self._rawdata.write(bytes(name[:0x3F], "iso-8859-1" if self.region != "NTSC-J" else "shift-jis"))

    @property
    @io_preserve
    def gameDescription(self) -> str:
        return _read_string(self._rawdata, 0x18E0 + (self.index * 0x140), 0x80, encoding="iso-8859-1" if self.region != "NTSC-J" else "shift-jis")

    @gameDescription.setter
    @io_preserve
    def gameDescription(self, name: str):
        self._rawdata.seek(0x18E0 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x80)
        self._rawdata.seek(0x18E0 + (self.index * 0x140))
        self._rawdata.write(bytes(name[:0x7F], "iso-8859-1" if self.region != "NTSC-J" else "shift-jis"))

    def getImage(self) -> Image:
        _image = self.rawImage
        img = Image.new("RGBA", (BNR.ImageWidth, BNR.ImageHeight))

        for yBlock in range(BNR.ImgTileHeight):
            for xBlock in range(BNR.ImgTileWidth):
                for iy in range(BNR.TileHeight):
                    for ix in range(BNR.TileWidth):
                        x = xBlock*BNR.TileWidth + ix
                        y = yBlock*BNR.TileHeight + iy

                        pixel = int.from_bytes(
                            _image.read(2), "big", signed=False)
                        if x < BNR.ImageWidth and y < BNR.ImageHeight:
                            img.putpixel((x, y), self.decode_pixel(pixel))

        return img

    def save_bnr(self, dest: Path):
        dest.write_bytes(self._rawdata.getvalue())

    def save_png(self, dest: Path):
        img = self.getImage()
        img.save(str(dest))

        f = dest.parent / (dest.stem + ".json")
        info = {}

        info["gamename"] = self.gameName
        info["gametitle"] = self.gameTitle
        info["developername"] = self.developerName
        info["developertitle"] = self.developerTitle
        info["description"] = self.gameDescription

        with f.open("w") as jsonFile:
            json.dump(info, jsonFile, indent=4)

    def load(self, f: Path, region: Regions = Regions.AMERICA, gameName: str = "", gameTitle: str = "", developerName: str = "", developerTitle: str = "", desc: str = "", overwrite: bool = False):
        self.regionID = region
        if f.suffix == ".bnr":
            self._rawdata = BytesIO(f.read_bytes())
            if overwrite:
                self.magic = region
                self.gameName = gameName
                self.gameTitle = gameTitle
                self.developerName = developerName
                self.developerTitle = developerTitle
                self.gameDescription = desc
        elif f.suffix in (".png", ".jpeg"):
            j = f.parent / (f.stem + ".json")

            if j.exists() and not overwrite:
                with j.open("r") as jsonFile:
                    info = json.load(jsonFile)

                self.gameName = info["gamename"]
                self.gameTitle = info["gametitle"]
                self.developerName = info["developername"]
                self.developerTitle = info["developertitle"]
                self.gameDescription = info["description"]
            else:
                self.gameName = gameName
                self.gameTitle = gameTitle
                self.developerName = developerName
                self.developerTitle = developerTitle
                self.gameDescription = desc

            self.magic = region

            self.rawImage = Image.open(f)


if __name__ == "__main__":
    parser = ArgumentParser(
        "BNR Parser", description="Tool to extract and compile bnr files")

    parser.add_argument("bnr", help="bnr file")
    parser.add_argument("img", help="png or jpeg image")
    parser.add_argument("-j", "--job",
                        help="Job to execute",
                        choices=[Jobs.EXTRACT, Jobs.COMPILE],
                        default=Jobs.COMPILE)
    parser.add_argument("-r", "--region",
                        help="Game region",
                        choices=["E", "P", "J"],
                        default="E")
    parser.add_argument("-g", "--gamename",
                        help="Game short name",
                        default="",
                        metavar="STR")
    parser.add_argument("-G", "--gametitle",
                        help="Game long name",
                        default="",
                        metavar="STR")
    parser.add_argument("-d", "--devname",
                        help="Developer short name",
                        default="",
                        metavar="STR")
    parser.add_argument("-D", "--devtitle",
                        help="Developer long name",
                        default="",
                        metavar="STR")
    parser.add_argument("--desc",
                        help="Game description",
                        default="",
                        metavar="STR")
    parser.add_argument("-o", "--overwrite",
                        help="Force arguments over json",
                        action="store_true")

    args = parser.parse_args()

    if args.region == "E":
        region = BNR.Regions.AMERICA
    elif args.region == "P":
        region = BNR.Regions.EUROPE
    elif args.region == "J":
        region = BNR.Regions.JAPAN
    else:
        raise NotImplementedError(
            f"Unknown region type {args.region} provided")

    if args.job == Jobs.COMPILE:
        bnr = BNR(Path(args.img).resolve(),
                  region=region,
                  gameName=args.gamename,
                  gameTitle=args.gametitle,
                  developerName=args.devname,
                  developerTitle=args.devtitle,
                  desc=args.desc,
                  overwrite=args.overwrite)

        bnr.save_bnr(Path(args.bnr).resolve())
    elif args.job == Jobs.EXTRACT:
        bnr = BNR(Path(args.bnr).resolve(), overwrite=args.overwrite)

        bnr.save_png(Path(args.img).resolve())
