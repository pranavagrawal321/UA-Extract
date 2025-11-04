from .base import BaseDeviceParser
from ua_extract.enums import DeviceType


class Console(BaseDeviceParser):
    __slots__ = ()
    DEVICE_TYPE = DeviceType.Console

    fixture_files = [
        'upstream/device/consoles.yml',
    ]


__all__ = [
    'Console',
]
