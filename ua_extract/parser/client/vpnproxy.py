from . import BaseClientParser
from ua_extract.enums import AppType


class VPNProxy(BaseClientParser):
    __slots__ = ()
    APP_TYPE = AppType.VpnProxy

    fixture_files = [
        'local/client/vpnproxy.yml',
    ]


__all__ = [
    'VPNProxy',
]
