import os
import shutil
import subprocess
import tempfile
import asyncio
from enum import Enum
from .source import main  # your async downloader

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
def update_with_git(self: Regexes):
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


@register(UpdateMethod.API)
def update_with_api(self: Regexes):
    print("[+] Updating regexes using GitHub API...")

    try:
        self._prepare_upstream_dir()
        asyncio.run(main(
            "https://github.com/matomo-org/device-detector/tree/master/regexes",
            self.upstream_path
        ))
        self._touch_init_file()
        print("[✓] Regexes updated successfully via API.")
    except Exception as e:
        print(f"[✗] Unexpected error during API update: {e}")
