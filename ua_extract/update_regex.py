import shutil
import asyncio
import aiohttp
import tempfile
import subprocess
from enum import Enum
from typing import Optional, Callable, Dict, List
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

ROOT_PATH = Path(__file__).resolve().parent


class UpdateMethod(Enum):
    GIT = "git"
    API = "api"


_method_registry: Dict[UpdateMethod, Callable] = {}


def register(method: UpdateMethod):
    def decorator(func):
        _method_registry[method] = func
        return func

    return decorator


class Regexes:
    def __init__(
        self,
        upstream_path: str = ROOT_PATH / "regexes" / "upstream",
        repo_url: str = "https://github.com/matomo-org/device-detector.git",
        branch: str = "master",
        sparse_dir: str = "regexes",
        sparse_fixtures_dir: str = "Tests/fixtures",
        fixtures_upstream_path: str = ROOT_PATH / "tests" / "fixtures" / "upstream",
        sparse_client_dir: str = "Tests/Parser/Client/fixtures",
        client_upstream_dir: str = ROOT_PATH
        / "tests"
        / "parser"
        / "fixtures"
        / "upstream"
        / "client",
        sparse_device_dir: str = "Tests/Parser/Device/fixtures",
        device_upstream_dir: str = ROOT_PATH
        / "tests"
        / "parser"
        / "fixtures"
        / "upstream"
        / "device",
        github_token: Optional[str] = None,
        message_callback: Optional[Callable[[str], None]] = None,
    ):
        self.upstream_path = self._validate_path(upstream_path)
        self.repo_url = repo_url
        self.branch = branch
        self.sparse_dir = sparse_dir
        self.sparse_fixtures_dir = sparse_fixtures_dir
        self.fixtures_upstream_path = self._validate_path(fixtures_upstream_path)
        self.sparse_client_dir = sparse_client_dir
        self.client_upstream_dir = self._validate_path(client_upstream_dir)
        self.sparse_device_dir = sparse_device_dir
        self.device_upstream_dir = self._validate_path(device_upstream_dir)
        self.github_token = github_token
        self.message_callback = message_callback or (lambda _: None)

    def _notify(self, message: str):
        self.message_callback(message)

    def _validate_path(self, path) -> Path:
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _backup_directory(self, path: Path):
        if path.exists():
            backup = path.with_suffix(path.suffix + ".backup")
            shutil.copytree(path, backup, dirs_exist_ok=True)

    def _backup_all_targets(self):
        for p in (
            self.upstream_path,
            self.fixtures_upstream_path,
            self.client_upstream_dir,
            self.device_upstream_dir,
        ):
            self._backup_directory(p)

    def _restore_directory(self, path: Path):
        backup = path.with_suffix(path.suffix + ".backup")
        if not backup.exists():
            self._notify(f"No backup found for {path}, skipping")
            return

        if path.exists():
            shutil.rmtree(path)

        shutil.copytree(backup, path)

    def rollback_regexes(self):
        self._notify("Rolling back regexes...")
        for p in (
            self.upstream_path,
            self.fixtures_upstream_path,
            self.client_upstream_dir,
            self.device_upstream_dir,
        ):
            self._restore_directory(p)
        self._notify("Rollback complete")

    def _clean_dir(self, path: Path):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    def update_regexes(self, method: str = "git", dry_run: bool = False):
        if dry_run:
            self._notify(f"[Dry Run] Would update regexes using {method}")
            return

        try:
            method_enum = UpdateMethod(method.lower())
        except ValueError:
            raise ValueError(f"Invalid method: {method}")

        updater = _method_registry.get(method_enum)
        if not updater:
            raise RuntimeError(f"No updater registered for {method_enum}")

        self._backup_all_targets()

        try:
            updater(self)
        except Exception:
            self._notify("Update failed — restoring backups")
            self.rollback_regexes()
            raise


@register(UpdateMethod.GIT)
def _update_with_git(self: Regexes):
    if shutil.which("git") is None:
        raise EnvironmentError(
            "Git is not available on this system. Please install Git and ensure it is in PATH."
        )

    self._notify("Updating regexes via Git...")

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                "--branch",
                self.branch,
                self.repo_url,
                tmp,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        subprocess.run(
            [
                "git",
                "-C",
                tmp,
                "sparse-checkout",
                "set",
                self.sparse_dir,
                self.sparse_fixtures_dir,
                self.sparse_client_dir,
                self.sparse_device_dir,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        mapping = [
            (Path(tmp) / self.sparse_dir, self.upstream_path),
            (Path(tmp) / self.sparse_fixtures_dir, self.fixtures_upstream_path),
            (Path(tmp) / self.sparse_client_dir, self.client_upstream_dir),
            (Path(tmp) / self.sparse_device_dir, self.device_upstream_dir),
        ]

        for src, dst in mapping:
            if not src.exists():
                raise FileNotFoundError(src)
            self._clean_dir(dst)
            shutil.copytree(src, dst, dirs_exist_ok=True)
            (dst / "__init__.py").touch()

    self._notify("Git update complete")


def _normalize_github_url(url: str):
    parsed = urlparse(url.strip())
    if parsed.netloc != "github.com":
        raise ValueError("Invalid GitHub URL")

    parts = parsed.path.strip("/").split("/")
    if len(parts) < 4 or parts[2] != "tree":
        raise ValueError("Expected GitHub tree URL")

    return {
        "owner": parts[0],
        "repo": parts[1],
        "branch": parts[3],
        "path": "/".join(parts[4:]),
    }


async def _check_rate_limit(session, token):
    headers = {"Authorization": f"token {token}"} if token else {}
    async with session.get("https://api.github.com/rate_limit", headers=headers) as r:
        data = await r.json()
        core = data.get("rate") or {}
        remaining = core.get("remaining", 0)
        if remaining < 5:
            reset = datetime.fromtimestamp(core.get("reset", 0), tz=timezone.utc)
            raise RuntimeError(f"Rate limit low ({remaining}), resets at {reset.isoformat()}")


async def _walk_contents(session, api_url, token, out):
    async with session.get(api_url) as r:
        r.raise_for_status()
        items = await r.json()

        if isinstance(items, dict):
            out.append(items)
            return

        for item in items:
            if item["type"] == "dir":
                await _walk_contents(session, item["url"], token, out)
            else:
                out.append(item)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(),
    retry=retry_if_exception_type(Exception),
)
async def _download(session, url, path):
    async with session.get(url) as r:
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(await r.read())


async def _api_download_tree(self, github_url, output_dir):
    meta = _normalize_github_url(github_url)
    api_url = (
        f"https://api.github.com/repos/{meta['owner']}/{meta['repo']}"
        f"/contents/{meta['path']}?ref={meta['branch']}"
    )

    headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}
    async with aiohttp.ClientSession(headers=headers) as session:
        await _check_rate_limit(session, self.github_token)

        contents: List[dict] = []
        await _walk_contents(session, api_url, self.github_token, contents)

        sem = asyncio.Semaphore(10)

        async def bounded(item):
            async with sem:
                await _download(
                    session,
                    item["download_url"],
                    Path(output_dir) / item["path"].split("/", 1)[1],
                )

        await asyncio.gather(*(bounded(i) for i in contents if i.get("download_url")))


@register(UpdateMethod.API)
def _update_with_api(self: Regexes):
    self._notify("Updating regexes via GitHub API...")

    tasks = [
        (
            "https://github.com/matomo-org/device-detector/tree/master/regexes",
            self.upstream_path,
        ),
        (
            "https://github.com/matomo-org/device-detector/tree/master/Tests/fixtures",
            self.fixtures_upstream_path,
        ),
        (
            "https://github.com/matomo-org/device-detector/tree/master/Tests/Parser/Client/fixtures",
            self.client_upstream_dir,
        ),
        (
            "https://github.com/matomo-org/device-detector/tree/master/Tests/Parser/Device/fixtures",
            self.device_upstream_dir,
        ),
    ]

    async def runner():
        for url, path in tasks:
            self._clean_dir(path)
            await _api_download_tree(self, url, path)
            (path / "__init__.py").touch()

    asyncio.run(runner())
    self._notify("API update complete")
