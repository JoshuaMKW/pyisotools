from __future__ import annotations

import json
from argparse import ArgumentParser
from functools import wraps
from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image

from pyisotools.iohelper import detect_encoding, read_string


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


class RGB5A1():

    TileWidth = 4
    TileHeight = 4

    @staticmethod
    def encode_pixel(pixel: tuple) -> int:
        """ RGB888 or RGBA8888 ONLY """
        red = (pixel[0] >> 3) & 0b11111
        green = (pixel[1] >> 3) & 0b11111
        blue = (pixel[2] >> 3) & 0b11111
        alpha = 1

        return (alpha << 15) | (red << 10) | (green << 5) | blue

    @staticmethod
    def decode_pixel(pixel: int) -> tuple:
        """ RGBA8888 ONLY """
        red = ((pixel >> 10) & 0b11111) << 3
        green = ((pixel >> 5) & 0b11111) << 3
        blue = (pixel & 0b11111) << 3
        alpha = 0xFF

        return (red, green, blue, alpha)


class RGB5A3():

    TileWidth = 4
    TileHeight = 4

    @staticmethod
    def encode_pixel(pixel: tuple) -> int:
        """ RGB888 or RGBA8888 ONLY """
        red = (pixel[0] >> 4) & 0b1111
        green = (pixel[1] >> 4) & 0b1111
        blue = (pixel[2] >> 4) & 0b1111
        if len(pixel) == 3:
            alpha = 0b111
        else:
            alpha = (pixel[3] >> 5) & 0b111

        return (alpha << 12) | (red << 8) | (green << 4) | blue

    @staticmethod
    def decode_pixel(pixel: int) -> tuple:
        """ RGBA8888 ONLY """
        red = ((pixel >> 8) & 0b1111) << 4
        green = ((pixel >> 4) & 0b1111) << 4
        blue = (pixel & 0b1111) << 4
        alpha = ((pixel >> 12) & 0b111) << 5

        return (red, green, blue, alpha)


class BNR(RGB5A3):
    class Regions:
        AMERICA = 0
        EUROPE = 1
        JAPAN = 2
        KOREA = 0

    ImageWidth = 96
    ImageHeight = 32

    ImgTileWidth = ImageWidth // RGB5A1.TileWidth
    ImgTileHeight = ImageHeight // RGB5A1.TileHeight

    def __init__(
        self,
        f: Path,
        region: Regions = Regions.AMERICA,
        gameName: str = "",
        gameTitle: str = "",
        developerName: str = "",
        developerTitle: str = "",
        desc: str = "",
        overwrite=False
    ):
        self._rawdata = BytesIO(
            b"\x00" * (0x1960 if region != BNR.Regions.EUROPE else 0x1FA0))
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
        if self.regionID == BNR.Regions.EUROPE:
            return "PAL"
        if self.regionID == BNR.Regions.JAPAN:
            return "NTSC-J"
        return "NTSC-K"

    @property
    @io_preserve
    def magic(self) -> str:
        self._rawdata.seek(0)
        _magic = self._rawdata.read(4).decode("iso-8859-1")
        if _magic not in {"BNR1", "BNR2"}:
            raise ValueError("BNR magic is invalid")
        return _magic

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
    def rawImage(self, _img: Union[bytes, BytesIO, Image.Image]):
        self._rawdata.seek(0x20)
        if isinstance(_img, bytes):
            self._rawdata.write(_img[:0x1800])
            return
        if isinstance(_img, BytesIO):
            self._rawdata.write(_img.getvalue()[:0x1800])
            return

        smallImg = _img.resize((BNR.ImageWidth, BNR.ImageHeight))
        for blockRow in range(BNR.ImgTileHeight):
            for blockColumn in range(BNR.ImgTileWidth):
                for tileRow in range(BNR.TileHeight):
                    for tileColumn in range(BNR.TileWidth):
                        column = blockColumn*BNR.TileWidth + tileColumn
                        row = blockRow*BNR.TileHeight + tileRow

                        pixel = smallImg.getpixel((column, row))
                        if column < BNR.ImageWidth and row < BNR.ImageHeight:
                            self._rawdata.write(self._encode_pixel(
                                pixel).to_bytes(2, "big", signed=False))

    @property
    @io_preserve
    def gameName(self) -> str:
        return read_string(self._rawdata, 0x1820 + (self.index * 0x140), 0x20)

    @gameName.setter
    @io_preserve
    def gameName(self, name: str):
        self._rawdata.seek(0x1820 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x20)
        self._rawdata.seek(0x1820 + (self.index * 0x140))
        self._rawdata.write(
            bytes(name[:0x1F], "shift-jis"))

    @property
    @io_preserve
    def developerName(self) -> str:
        return read_string(self._rawdata, 0x1840 + (self.index * 0x140), 0x20)

    @developerName.setter
    @io_preserve
    def developerName(self, name: str):
        self._rawdata.seek(0x1840 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x20)
        self._rawdata.seek(0x1840 + (self.index * 0x140))
        self._rawdata.write(
            bytes(name[:0x1F], "shift-jis"))

    @property
    @io_preserve
    def gameTitle(self) -> str:
        return read_string(self._rawdata, 0x1860 + (self.index * 0x140), 0x40)

    @gameTitle.setter
    @io_preserve
    def gameTitle(self, name: str):
        self._rawdata.seek(0x1860 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x40)
        self._rawdata.seek(0x1860 + (self.index * 0x140))
        self._rawdata.write(
            bytes(name[:0x3F], "shift-jis"))

    @property
    @io_preserve
    def developerTitle(self) -> str:
        return read_string(self._rawdata, 0x18A0 + (self.index * 0x140), 0x40)

    @developerTitle.setter
    @io_preserve
    def developerTitle(self, name: str):
        self._rawdata.seek(0x18A0 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x40)
        self._rawdata.seek(0x18A0 + (self.index * 0x140))
        self._rawdata.write(
            bytes(name[:0x3F], "shift-jis"))

    @property
    @io_preserve
    def gameDescription(self) -> str:
        return read_string(self._rawdata, 0x18E0 + (self.index * 0x140), 0x80)

    @gameDescription.setter
    @io_preserve
    def gameDescription(self, name: str):
        self._rawdata.seek(0x18E0 + (self.index * 0x140))
        self._rawdata.write(b"\x00" * 0x80)
        self._rawdata.seek(0x18E0 + (self.index * 0x140))
        self._rawdata.write(
            bytes(name[:0x7F], "shift-jis"))

    def get_image(self) -> Image.Image:
        _image = self.rawImage
        img = Image.new("RGBA", (BNR.ImageWidth, BNR.ImageHeight))

        for blockRow in range(BNR.ImgTileHeight):
            for blockColumn in range(BNR.ImgTileWidth):
                for tileRow in range(BNR.TileHeight):
                    for tileColumn in range(BNR.TileWidth):
                        column = blockColumn*BNR.TileWidth + tileColumn
                        row = blockRow*BNR.TileHeight + tileRow

                        pixel = int.from_bytes(
                            _image.read(2), "big", signed=False)
                        if column < BNR.ImageWidth and row < BNR.ImageHeight:
                            img.putpixel(
                                (column, row), self._decode_pixel(pixel))

        return img

    def save_bnr(self, dest: Path):
        dest.write_bytes(self._rawdata.getvalue())

    def save_png(self, dest: Path):
        img.save(str(dest))
        img = self.get_image()

    def load(
        self,
        f: Path,
        region: Regions = Regions.AMERICA,
        gameName: str = "",
        gameTitle: str = "",
        developerName: str = "",
        developerTitle: str = "",
        desc: str = "",
        overwrite=False
    ):
        if f.suffix == ".bnr":
            self._rawdata = BytesIO(f.read_bytes())
        elif f.suffix in (".png", ".jpeg"):
            self.rawImage = Image.open(f)

        self.regionID = region
        if overwrite:
            self.magic = region
            self.gameName = gameName
            self.gameTitle = gameTitle
            self.developerName = developerName
            self.developerTitle = developerTitle
            self.gameDescription = desc

    @staticmethod
    def _encode_pixel(pixel: tuple):
        if len(pixel) == 3:
            return RGB5A1.encode_pixel(pixel)
        return RGB5A3.encode_pixel(pixel)

    @staticmethod
    def _decode_pixel(pixel: int):
        if (pixel >> 15) & 1:
            return RGB5A1.decode_pixel(pixel)
        return RGB5A3.decode_pixel(pixel)

    def __len__(self) -> int:
        return len(self._rawdata.getbuffer())


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
        REGION = BNR.Regions.AMERICA
    elif args.region == "P":
        REGION = BNR.Regions.EUROPE
    elif args.region == "J":
        REGION = BNR.Regions.JAPAN
    else:
        raise NotImplementedError(
            f"Unknown region type {args.region} provided")

    if args.job == Jobs.COMPILE:
        bnr = BNR(Path(args.img).resolve(),
                  region=REGION,
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
