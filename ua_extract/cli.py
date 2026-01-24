import sys
import json
import typer
import warnings
from pathlib import Path
from . import DeviceDetector
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union
from .update_regex import Regexes, UpdateMethod

ROOT_PATH = Path(__file__).parent.resolve()

app = typer.Typer(
    name="ua_extract",
    help="UA-Extract CLI for updating regex and fixture files",
)


def message_callback(message: str):
    print(message, file=sys.stderr)


@dataclass(frozen=True)
class ParsedDevice:
    is_bot: bool
    os_name: Optional[str]
    os_version: Optional[str]
    engine: Optional[Union[Dict[str, Any], str]]
    device_brand: Optional[str]
    device_model: Optional[str]
    device_type: Optional[str]
    secondary_client_name: Optional[str]
    secondary_client_type: Optional[str]
    secondary_client_version: Optional[str]
    bot_name: Optional[str]
    client_name: Optional[str]
    client_type: Optional[str]
    client_application_id: Optional[str]
    is_television: Optional[bool]
    uses_mobile_browser: Optional[bool]
    is_mobile: Optional[bool]
    is_desktop: Optional[bool]
    is_feature_phone: Optional[bool]
    preferred_client_name: Optional[str]
    preferred_client_version: Optional[str]
    preferred_client_type: Optional[str]


@app.command(name="update_regexes", help="Update regexes from upstream repository")
def update_regexes(
    path: Path = ROOT_PATH / "regexes" / "upstream",
    repo: str = "https://github.com/matomo-org/device-detector.git",
    branch: str = "master",
    method: UpdateMethod = UpdateMethod.GIT,
    no_progress: bool = typer.Option(
        False,
        "--no-progress",
        help="(DEPRECATED) Progress is always disabled. This option will be removed.",
        hidden=True,
    ),
):
    if no_progress:
        warnings.warn(
            "--no-progress is deprecated and has no effect; it will be removed",
            FutureWarning,
            stacklevel=2,
        )
    regexes = Regexes(
        upstream_path=str(path),
        repo_url=repo,
        branch=branch,
        message_callback=message_callback,
    )
    regexes.update_regexes(method=method.value)


@app.command(name="rollback_regexes", help="Rollback regexes to last known good state")
def rollback_regexes():
    Regexes(message_callback=print).rollback_regexes()


def parse_device(ua: str, headers) -> ParsedDevice:
    d = DeviceDetector(ua, headers=headers).parse()

    return ParsedDevice(
        is_bot=d.is_bot(),
        os_name=d.os_name(),
        os_version=d.os_version(),
        engine=d.engine(),
        device_brand=d.device_brand(),
        device_model=d.device_model(),
        device_type=d.device_type(),
        secondary_client_name=d.secondary_client_name(),
        secondary_client_type=d.secondary_client_type(),
        secondary_client_version=d.secondary_client_version(),
        bot_name=d.bot_name(),
        client_name=d.client_name(),
        client_type=d.client_type(),
        client_application_id=d.client_application_id(),
        is_television=d.is_television(),
        uses_mobile_browser=d.uses_mobile_browser(),
        is_mobile=d.is_mobile(),
        is_desktop=d.is_desktop(),
        is_feature_phone=d.is_feature_phone(),
        preferred_client_name=d.preferred_client_name(),
        preferred_client_version=d.preferred_client_version(),
        preferred_client_type=d.preferred_client_type(),
    )


@app.command(help="Parse a user-agent along with headers")
def parse(
    ua: str = typer.Option(..., "--ua", help="User-Agent string"),
    headers: Optional[str] = typer.Option(
        None,
        "--headers",
        help="Headers as JSON or KEY=VALUE,KEY=VALUE",
    ),
):
    try:
        parsed_headers: Optional[Dict[str, str]] = (
            json.loads(headers) if headers is not None else None
        )
        if parsed_headers is not None and not isinstance(parsed_headers, dict):
            raise ValueError
    except Exception:
        raise typer.BadParameter('--headers must be a JSON object, e.g. {"Accept":"*/*"}')

    parsed = parse_device(ua, parsed_headers)
    print(json.dumps(asdict(parsed), indent=2))
