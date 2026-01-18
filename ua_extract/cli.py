from pathlib import Path
import sys
import typer

from .update_regex import Regexes, UpdateMethod
from . import DeviceDetector
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union
import json

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


@app.command(name="update_regexes")
def update_regexes(
    path: Path = ROOT_PATH / "regexes" / "upstream",
    repo: str = "https://github.com/matomo-org/device-detector.git",
    branch: str = "master",
    method: UpdateMethod = UpdateMethod.GIT,
):
    regexes = Regexes(
        upstream_path=str(path),
        repo_url=repo,
        branch=branch,
        message_callback=message_callback,
    )
    regexes.update_regexes(method=method.value)


@app.command(name="rollback_regexes")
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
    )


@app.command()
def parse(
    ua: str = typer.Option(..., "--ua", help="User-Agent string"),
    headers: Optional[str] = typer.Option(
        None,
        "--headers",
        help="Headers as JSON or KEY=VALUE,KEY=VALUE",
    ),
):
    parsed = parse_device(ua, eval(headers))
    print(json.dumps(asdict(parsed), indent=2))
