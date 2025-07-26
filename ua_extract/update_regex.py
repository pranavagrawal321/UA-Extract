import os
import shutil
import subprocess
import tempfile
import asyncio
from enum import Enum
import aiohttp
from urllib.parse import urlparse

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
    def __init__(
        self,
        upstream_path: str = os.path.join(ROOT_PATH, "regexes", "upstream"),
        repo_url: str = "https://github.com/matomo-org/device-detector.git",
        branch: str = "master",
        sparse_dir: str = "regexes",
        cleanup: bool = True
    ):
        self.upstream_path = upstream_path
        self.repo_url = repo_url
        self.branch = branch
        self.sparse_dir = sparse_dir
        self.cleanup = cleanup

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
    print("[+] Updating regexes using Git...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run([
                "git", "clone",
                "--depth", "1",
                "--filter=blob:none",
                "--sparse",
                "--branch", self.branch,
                self.repo_url,
                temp_dir
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            subprocess.run([
                "git", "-C", temp_dir,
                "sparse-checkout", "set", self.sparse_dir
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            src_dir = os.path.join(temp_dir, self.sparse_dir)
            self._prepare_upstream_dir()

            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(self.upstream_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)

        self._touch_init_file()
        print("[✓] Regexes updated successfully via Git.")

    except subprocess.CalledProcessError:
        print("[✗] Git operation failed.")
    except Exception as e:
        print(f"[✗] Unexpected error during Git update: {e}")


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


async def _get_contents(content_url):
    download_urls = []

    async with aiohttp.ClientSession() as session:
        async with session.get(content_url) as response:
            if response.ok:
                response = await response.json()
                if isinstance(response, dict):
                    return {
                        "name": response.get("name"),
                        "download_url": response.get("download_url"),
                        "content_blob": response.get("content"),
                    }
                for resp in response:
                    content_name = resp.get("name")
                    content_type = resp.get("type")
                    content_self_url = resp.get("url")
                    content_download_url = resp.get("download_url")
                    if content_type == "dir":
                        sub_content = await _get_contents(content_self_url)
                        for sub_item in sub_content:
                            sub_item["name"] = f"{content_name}/{sub_item.get('name')}"
                            download_urls.append(sub_item)
                    elif content_type == "file":
                        download_urls.append(
                            {"name": content_name, "download_url": content_download_url}
                        )
    return download_urls


async def _download_content(download_url, output_file):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                response.raise_for_status()
                resp_content = await response.read()
                with open(output_file, mode="wb") as file:
                    file.write(resp_content)
    except BaseException:
        print(f":warning: Failed to download {download_url!r}. Skipping this file!")


async def _download_with_progress(download_url, content_filename):
    await _download_content(download_url, content_filename)


async def _download_from_github_api(github_url, output_dir=None):
    repo_data = _normalize_github_url(github_url)
    owner = repo_data.get("owner")
    repo = repo_data.get("repo")
    branch = repo_data.get("branch")
    root_target = repo_data.get("target")
    root_target_path = output_dir

    target_path = repo_data.get("target_path")
    content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{target_path}?ref={branch}"

    contents = await _get_contents(content_url)

    if isinstance(contents, dict):  # single file
        await _download_content(contents.get("download_url"), os.path.join(root_target_path, root_target))
        return

    os.makedirs(root_target_path, exist_ok=True)
    download_tasks = []

    for content in contents:
        content_path = content.get("name")
        download_url = content.get("download_url")
        if not download_url:
            continue

        content_parentdir = os.path.dirname(content_path)
        content_parentdir = os.path.join(root_target_path, content_parentdir)
        content_filename = os.path.join(root_target_path, content_path)

        os.makedirs(content_parentdir, exist_ok=True)
        task = asyncio.create_task(_download_with_progress(download_url, content_filename))
        download_tasks.append(task)

    await asyncio.gather(*download_tasks)


@register(UpdateMethod.API)
def _update_with_api(self: Regexes):
    print("[+] Updating regexes using GitHub API...")

    try:
        self._prepare_upstream_dir()
        asyncio.run(_download_from_github_api(
            "https://github.com/matomo-org/device-detector/tree/master/regexes",
            self.upstream_path
        ))
        self._touch_init_file()
        print("[✓] Regexes updated successfully via API.")
    except Exception as e:
        print(f"[✗] Unexpected error during API update: {e}")
