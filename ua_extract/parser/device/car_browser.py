from .base import BaseDeviceParser
from ua_extract.enums import DeviceType


class CarBrowser(BaseDeviceParser):
    __slots__ = ()
    DEVICE_TYPE = DeviceType.CarBrowser

    fixture_files = [
        'upstream/device/car_browsers.yml',
    ]


__all__ = [
    'CarBrowser',
]
