from . import BaseClientParser
from ua_extract.enums import AppType


class MediaPlayer(BaseClientParser):
    __slots__ = ()
    APP_TYPE = AppType.MediaPlayer

    fixture_files = [
        'upstream/client/mediaplayers.yml',
    ]


__all__ = [
    'MediaPlayer',
]
