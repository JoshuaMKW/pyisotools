from dataclasses import dataclass
from pyisotools.security.signature import SignatureRSA2048

@dataclass(eq=True)
class TMDHeader():
  signature: SignatureRSA2048
  tmdVersion: int
  caCrlVersion: int
  signerCrlVersion: int
  iosID: int
  titleID: int
  titleFlags: int
  groupID: int
  zero: int
  region: int
  ratings: bytes #16 len
  reserved: bytes #12 len
  ipcMask: bytes #12 len
  reserved2: bytes #18 len
  accessRights: int
  titleVersion: int
  numContents: int
  bootIndex: int