from . import BaseClientParser
from ua_extract.enums import AppType


class Messaging(BaseClientParser):
    __slots__ = ()
    APP_TYPE = AppType.Messaging


__all__ = [
    'Messaging',
]
