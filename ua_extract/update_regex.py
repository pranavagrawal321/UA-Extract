import os
import shutil
import asyncio
import aiohttp
import tempfile
import subprocess
from enum import Enum
from typing import Optional
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TransferSpeedColumn

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

class UpdateMethod(Enum):
    GIT = "git"
    API = "api"

_method_registry = {}

def register(method: UpdateMethod):
    def decorator(func):
        _method_registry[method] = func
        return func
    return decorator

class Regexes:
    """Manages updating regexes and fixtures from the Matomo Device Detector repository.

    Args:
        upstream_path (str): Local path to store regex files.
        repo_url (str): GitHub repository URL (default: Matomo Device Detector).
        branch (str): Repository branch (default: master).
        sparse_dir (str): Directory in repo for regexes.
        sparse_fixtures_dir (str): Directory in repo for fixtures.
        fixtures_upstream_path (str): Local path for fixtures.
        sparse_client_dir (str): Directory in repo for client fixtures.
        client_upstream_dir (str): Local path for client fixtures.
        sparse_device_dir (str): Directory in repo for device fixtures.
        device_upstream_dir (str): Local path for device fixtures.
        cleanup (bool): Whether to remove existing directories before updating.
        github_token (Optional[str]): GitHub token for API access.
        message_callback (Optional[callable]): Function to handle messages (default: None).
    """
    def __init__(
        self,
        upstream_path: str = os.path.join(ROOT_PATH, "regexes", "upstream"),
        repo_url: str = "https://github.com/matomo-org/device-detector.git",
        branch: str = "master",
        sparse_dir: str = "regexes",
        sparse_fixtures_dir: str = "Tests/fixtures",
        fixtures_upstream_path: str = os.path.join(ROOT_PATH, "tests", "fixtures", "upstream"),
        sparse_client_dir: str = "Tests/Parser/Client/fixtures",
        client_upstream_dir: str = os.path.join(ROOT_PATH, "tests", "parser", "fixtures", "upstream", "client"),
        sparse_device_dir: str = "Tests/Parser/Device/fixtures",
        device_upstream_dir: str = os.path.join(ROOT_PATH, "tests", "parser", "fixtures", "upstream", "device"),
        cleanup: bool = True,
        github_token: Optional[str] = None,
        message_callback: Optional[callable] = None
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
        self.cleanup = cleanup
        self.github_token = github_token
        self.message_callback = message_callback or (lambda x: None)

    def _notify(self, message: str):
        """Send a message to the callback function."""
        self.message_callback(message)

    def _validate_path(self, path: str) -> Path:
        """Validate and resolve a filesystem path."""
        path = Path(path).resolve()
        if not path.is_dir() and not path.parent.exists():
            self._notify(f"Invalid path: {path}")
            raise ValueError(f"Invalid path: {path}")
        return path

    def _backup_directory(self, path: str):
        """Back up a directory before overwriting."""
        if os.path.exists(path):
            backup_path = f"{path}.backup"
            shutil.copytree(path, backup_path, dirs_exist_ok=True)
            self._notify(f"Backed up {path} to {backup_path}")

    def _prepare_upstream_dir(self):
        """Prepare the upstream directory, optionally cleaning it."""
        if self.cleanup and os.path.exists(self.upstream_path):
            self._backup_directory(self.upstream_path)
            shutil.rmtree(self.upstream_path)
        os.makedirs(self.upstream_path, exist_ok=True)

    def _touch_init_file(self):
        """Create an empty __init__.py file."""
        open(os.path.join(self.upstream_path, "__init__.py"), "a").close()

    def update_regexes(self, method: str = "git", dry_run: bool = False):
        """Update regexes and fixtures using the specified method.

        Args:
            method (str): Update method ("git" or "api").
            dry_run (bool): Simulate the update without modifying the filesystem.
        """
        if dry_run:
            self._notify(f"[Dry Run] Would update regexes using {method}")
            return

        try:
            method_enum = UpdateMethod(method.lower())
        except ValueError:
            self._notify(f"Invalid method: {method}. Allowed: {[m.value for m in UpdateMethod]}")
            raise ValueError(f"Invalid method: {method}. Allowed: {[m.value for m in UpdateMethod]}")

        func = _method_registry.get(method_enum)
        if not func:
            self._notify(f"No update function registered for method: {method_enum}")
            raise ValueError(f"No update function registered for method: {method_enum}")
        func(self)

@register(UpdateMethod.GIT)
def _update_with_git(self: Regexes):
    """Update regexes using Git sparse checkout."""
    self._notify("[+] Updating regexes using Git...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir, Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn()
        ) as progress:
            steps = [
                ("Cloning repository...", 4),
                ("Setting sparse-checkout...", 1),
                ("Copying files...", 3),
                ("Finalizing...", 1)
            ]
            task = progress.add_task("[cyan]Git Update", total=sum(s[1] for s in steps))

            subprocess.run([
                "git", "clone",
                "--depth", "1",
                "--filter=blob:none",
                "--sparse",
                "--branch", self.branch,
                self.repo_url,
                temp_dir
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            progress.advance(task, 4)

            subprocess.run([
                "git", "-C", temp_dir,
                "sparse-checkout", "set",
                self.sparse_dir,
                self.sparse_fixtures_dir,
                self.sparse_client_dir,
                self.sparse_device_dir
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            progress.advance(task, 1)

            mapping = [
                (os.path.join(temp_dir, self.sparse_dir), self.upstream_path),
                (os.path.join(temp_dir, self.sparse_fixtures_dir), self.fixtures_upstream_path),
                (os.path.join(temp_dir, self.sparse_client_dir), self.client_upstream_dir),
                (os.path.join(temp_dir, self.sparse_device_dir), self.device_upstream_dir),
            ]

            for src_dir, dst_dir in mapping:
                if not os.path.exists(src_dir):
                    self._notify(f"Expected directory {src_dir} not found in repository")
                    raise FileNotFoundError(f"Expected directory {src_dir} not found in repository")

                if self.cleanup and os.path.exists(dst_dir):
                    self._backup_directory(dst_dir)
                    shutil.rmtree(dst_dir)
                os.makedirs(dst_dir, exist_ok=True)

                for item in os.listdir(src_dir):
                    s = os.path.join(src_dir, item)
                    d = os.path.join(dst_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
            progress.advance(task, 3)

            for _, dst_dir in mapping:
                open(os.path.join(dst_dir, "__init__.py"), "a").close()
            progress.advance(task, 1)

        self._notify("Regexes updated successfully via Git")
    except subprocess.CalledProcessError as e:
        self._notify(f"Git operation failed: {e.stderr.decode()}")
        raise RuntimeError(f"Git operation failed: {e.stderr.decode()}") from e
    except Exception as e:
        self._notify(f"[✗] Unexpected error during Git update: {e}")
        raise

def _normalize_github_url(github_url: str):
    """Normalize and validate a GitHub URL."""
    github_url = github_url.strip()
    if not github_url.lower().startswith("https://github.com/"):
        raise ValueError("Not a valid GitHub URL")

    parsed_url = urlparse(github_url)
    parts = parsed_url.path.strip("/").split("/")

    if len(parts) < 5 or parts[2] != "tree":
        raise ValueError("URL must be in format: https://github.com/user/repo/tree/branch/path")

    owner, repo, _, branch = parts[:4]
    target_path = "/".join(parts[4:])
    target = parts[-1]

    return {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "target": target,
        "target_path": target_path,
    }

async def _check_rate_limit(session, token):
    """Check GitHub API rate limit."""
    headers = {"Authorization": f"token {token}"} if token else {}
    async with session.get("https://api.github.com/rate_limit", headers=headers) as response:
        data = await response.json()
        remaining = data["rate"]["remaining"]
        if remaining < 10:
            reset_time = data["rate"]["reset"]
            reset_time = datetime.utcfromtimestamp(int(reset_time)).strftime('%Y-%m-%d %H:%M:%S UTC')
            raise RuntimeError(f"Low rate limit remaining: {remaining}. Reset at: {reset_time}")

async def _get_contents(self, content_url, token=None):
    """Fetch contents from GitHub API."""
    download_urls = []
    headers = {"Authorization": f"token {token}"} if token else {}

    async with aiohttp.ClientSession(headers=headers) as session:
        await _check_rate_limit(session, token)
        async with session.get(content_url) as response:
            if response.status == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "0")
                reset_time = response.headers.get("X-RateLimit-Reset")
                if reset_time:
                    reset_time = datetime.utcfromtimestamp(int(reset_time)).strftime('%Y-%m-%d %H:%M:%S UTC')
                self._notify(f"Rate limit reached. Remaining: {remaining}. Reset at: {reset_time}")
                raise RuntimeError("GitHub API rate limit exceeded")

            if response.ok:
                response_data = await response.json()
                if isinstance(response_data, dict):
                    return [{
                        "name": response_data.get("name"),
                        "download_url": response_data.get("download_url"),
                        "content_blob": response_data.get("content"),
                    }]

                for resp in response_data:
                    name = resp.get("name")
                    content_type = resp.get("type")
                    self_url = resp.get("url")
                    download_url = resp.get("download_url")
                    if content_type == "dir":
                        sub = await _get_contents(self, self_url, token)
                        for item in sub:
                            item["name"] = f"{name}/{item.get('name')}"
                            download_urls.append(item)
                    elif content_type == "file":
                        download_urls.append({"name": name, "download_url": download_url})
    return download_urls

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def _download_content(download_url, output_file, token=None):
    """Download a file from a URL."""
    headers = {"Authorization": f"token {token}"} if token else {}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(download_url) as response:
            response.raise_for_status()
            content = await response.read()
            with open(output_file, "wb") as f:
                f.write(content)

async def _download_with_progress(self, download_url, content_filename, progress, task, token=None):
    """Download a file with progress tracking."""
    await _download_content(download_url, content_filename, token)
    progress.advance(task)

async def _download_from_github_api(self, github_url, output_dir=None, token=None, max_concurrent=10):
    """Download files from GitHub API with concurrency limit."""
    repo_data = _normalize_github_url(github_url)
    owner = repo_data["owner"]
    repo = repo_data["repo"]
    branch = repo_data["branch"]
    root_target_path = output_dir
    target_path = repo_data["target_path"]

    content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{target_path}?ref={branch}"
    contents = await _get_contents(self, content_url, token)

    os.makedirs(root_target_path, exist_ok=True)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%",
        TransferSpeedColumn(), TimeElapsedColumn()
    ) as progress:
        tasks = []
        task = progress.add_task("[cyan]Api Update", total=len(contents))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded_download(download_url, filename, progress, task, token):
            async with semaphore:
                await _download_with_progress(self, download_url, filename, progress, task, token)

        for content in contents:
            name = content.get("name")
            download_url = content.get("download_url")
            if not download_url:
                continue

            parent = os.path.dirname(name)
            os.makedirs(os.path.join(root_target_path, parent), exist_ok=True)
            filename = os.path.join(root_target_path, name)

            coro = _bounded_download(download_url, filename, progress, task, token)
            tasks.append(asyncio.create_task(coro))

        await asyncio.gather(*tasks)

@register(UpdateMethod.API)
def _update_with_api(self: Regexes):
    """Update regexes using GitHub API."""
    self._notify("[+] Updating regexes using GitHub API...")
    try:
        tasks = [
            ("https://github.com/matomo-org/device-detector/tree/master/regexes", self.upstream_path),
            ("https://github.com/matomo-org/device-detector/tree/master/Tests/fixtures", self.fixtures_upstream_path),
            ("https://github.com/matomo-org/device-detector/tree/master/Tests/Parser/Client/fixtures", self.client_upstream_dir),
            ("https://github.com/matomo-org/device-detector/tree/master/Tests/Parser/Device/fixtures", self.device_upstream_dir),
        ]

        loop = asyncio.get_event_loop()
        for url, path in tasks:
            if self.cleanup and os.path.exists(path):
                self._backup_directory(path)
                shutil.rmtree(path)
            os.makedirs(path, exist_ok=True)
            if loop.is_running():
                loop.create_task(_download_from_github_api(self, url, path, self.github_token))
            else:
                asyncio.run(_download_from_github_api(self, url, path, self.github_token))
            open(os.path.join(path, "__init__.py"), "a").close()

        self._notify("Regexes updated successfully via API")
    except Exception as e:
        self._notify(f"[✗] Unexpected error during API update: {e}")
        raise