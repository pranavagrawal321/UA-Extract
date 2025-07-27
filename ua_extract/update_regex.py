import os
import shutil
import asyncio
import aiohttp
import logging
import tempfile
import subprocess
from enum import Enum
from typing import Optional
from urllib.parse import urlparse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TransferSpeedColumn


ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    def __init__(
        self,
        upstream_path: str = os.path.join(ROOT_PATH, "regexes", "upstream"),
        repo_url: str = "https://github.com/matomo-org/device-detector.git",
        branch: str = "master",
        sparse_dir: str = "regexes",
        cleanup: bool = True,
        github_token: Optional[str] = None
    ):
        self.upstream_path = upstream_path
        self.repo_url = repo_url
        self.branch = branch
        self.sparse_dir = sparse_dir
        self.cleanup = cleanup
        self.github_token = github_token

    def update_regexes(self, method: str = "git"):
        try:
            method_enum = UpdateMethod(method.lower())
        except ValueError:
            raise ValueError(f"Invalid method: {method}. Allowed: {[m.value for m in UpdateMethod]}")

        func = _method_registry.get(method_enum)
        if not func:
            raise ValueError(f"No update function registered for method: {method_enum}")
        func(self)

    def _prepare_upstream_dir(self):
        if os.path.exists(self.upstream_path):
            shutil.rmtree(self.upstream_path)
        os.makedirs(self.upstream_path, exist_ok=True)

    def _touch_init_file(self):
        open(os.path.join(self.upstream_path, "__init__.py"), "a").close()


@register(UpdateMethod.GIT)
def _update_with_git(self: Regexes):
    logger.info("[+] Updating regexes using Git...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir, Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn()
        ) as progress:

            steps = [
                ("Cloning repository...", 1),
                ("Setting sparse-checkout...", 1),
                ("Copying files...", 1),
                ("Finalizing...", 1)
            ]
            task = progress.add_task("[cyan]Git Update Progress", total=sum(s[1] for s in steps))

            subprocess.run([
                "git", "clone",
                "--depth", "1",
                "--filter=blob:none",
                "--sparse",
                "--branch", self.branch,
                self.repo_url,
                temp_dir
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            progress.advance(task)

            subprocess.run([
                "git", "-C", temp_dir,
                "sparse-checkout", "set", self.sparse_dir
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            progress.advance(task)

            src_dir = os.path.join(temp_dir, self.sparse_dir)
            self._prepare_upstream_dir()

            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(self.upstream_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            progress.advance(task)

            self._touch_init_file()
            progress.advance(task)

        logger.info("Regexes updated successfully via Git")
    except subprocess.CalledProcessError:
        logger.error("Git operation failed")
    except Exception as e:
        logger.exception(f"[✗] Unexpected error during Git update: {e}")


def _normalize_github_url(github_url: str):
    github_url = github_url.strip()
    if not github_url.lower().startswith("https://github.com/"):
        raise ValueError("Not a valid Github URL")

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


async def _get_contents(content_url, token=None):
    download_urls = []
    headers = {"Authorization": f"token {token}"} if token else {}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(content_url) as response:
            if response.status == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "0")
                reset_time = response.headers.get("X-RateLimit-Reset")
                logger.warning(f"Rate limit reached. Remaining: {remaining}. Reset at: {reset_time}")
                raise RuntimeError("GitHub API rate limit exceeded")

            if response.ok:
                response = await response.json()
                if isinstance(response, dict):
                    return [{
                        "name": response.get("name"),
                        "download_url": response.get("download_url"),
                        "content_blob": response.get("content"),
                    }]

                for resp in response:
                    name = resp.get("name")
                    content_type = resp.get("type")
                    self_url = resp.get("url")
                    download_url = resp.get("download_url")
                    if content_type == "dir":
                        sub = await _get_contents(self_url, token)
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
    headers = {"Authorization": f"token {token}"} if token else {}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(download_url) as response:
            response.raise_for_status()
            content = await response.read()
            with open(output_file, "wb") as f:
                f.write(content)


async def _download_with_progress(download_url, content_filename, progress, task, token=None):
    await _download_content(download_url, content_filename, token)
    progress.advance(task)


async def _download_from_github_api(github_url, output_dir=None, token=None):
    repo_data = _normalize_github_url(github_url)
    owner = repo_data["owner"]
    repo = repo_data["repo"]
    branch = repo_data["branch"]
    root_target_path = output_dir
    target_path = repo_data["target_path"]

    content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{target_path}?ref={branch}"
    contents = await _get_contents(content_url, token)

    os.makedirs(root_target_path, exist_ok=True)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%",
        TransferSpeedColumn(), TimeElapsedColumn()
    ) as progress:
        tasks = []
        task = progress.add_task("[cyan]Downloading files...", total=len(contents))

        for content in contents:
            name = content.get("name")
            download_url = content.get("download_url")
            if not download_url:
                continue

            parent = os.path.dirname(name)
            os.makedirs(os.path.join(root_target_path, parent), exist_ok=True)
            filename = os.path.join(root_target_path, name)

            coro = _download_with_progress(download_url, filename, progress, task, token)
            tasks.append(asyncio.create_task(coro))

        await asyncio.gather(*tasks)


@register(UpdateMethod.API)
def _update_with_api(self: Regexes):
    logger.info("[+] Updating regexes using GitHub API...")
    try:
        self._prepare_upstream_dir()
        asyncio.run(_download_from_github_api(
            "https://github.com/matomo-org/device-detector/tree/master/regexes",
            self.upstream_path,
            token=self.github_token
        ))
        self._touch_init_file()
        logger.info("Regexes updated successfully via API")
    except Exception as e:
        logger.exception(f"[✗] Unexpected error during API update: {e}")
