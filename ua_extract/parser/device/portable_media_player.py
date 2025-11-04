from .base import BaseDeviceParser
from ua_extract.enums import DeviceType


class PortableMediaPlayer(BaseDeviceParser):
    __slots__ = ()
    DEVICE_TYPE = DeviceType.PortableMediaPlayer

    fixture_files = [
        'upstream/device/portable_media_player.yml',
    ]


__all__ = [
    'PortableMediaPlayer',
]
