"""Detect the real on-disk spreadsheet format from magic bytes.

LinkedIn sometimes serves an XLS (OLE2 / BIFF) payload with an ``.xlsx``
extension, or an XLSX (ZIP) with ``.xls``. We trust the bytes, not the name,
so the correct pandas engine is chosen.
"""
from __future__ import annotations

from enum import Enum

# OLE2 Compound Document (legacy .xls / BIFF)
_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
# ZIP container (OOXML .xlsx)
_ZIP_MAGIC = b"PK\x03\x04"


class SpreadsheetFormat(str, Enum):
    XLSX = "xlsx"
    XLS = "xls"
    UNKNOWN = "unknown"

    @property
    def engine(self) -> str | None:
        # Legacy .xls (BIFF/OLE2) is read with calamine — a fast, dependency-light
        # Rust reader — instead of xlrd (which some networks block on security
        # grounds). .xlsx stays on openpyxl.
        return {"xlsx": "openpyxl", "xls": "calamine"}.get(self.value)


def detect_format(data: bytes) -> SpreadsheetFormat:
    head = data[:8]
    if head.startswith(_ZIP_MAGIC):
        return SpreadsheetFormat.XLSX
    if head.startswith(_OLE2_MAGIC):
        return SpreadsheetFormat.XLS
    return SpreadsheetFormat.UNKNOWN
