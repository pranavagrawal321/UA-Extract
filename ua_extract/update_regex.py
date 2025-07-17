import os
import shutil
import subprocess
import tempfile
import sys
import logging

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

class Regexes:
    def __init__(
        self,
        upstream_path: str = ROOT_PATH + "/regexes/upstream",
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

    def update_regexes(self):
        logger.info("Updating regexes...")

        try:
            with tempfile.TemporaryDirectory() as temp:
                subprocess.run([
                    "git", "clone",
                    "--depth", "1",
                    "--filter=blob:none",
                    "--sparse",
                    "--branch", self.branch,
                    self.repo_url,
                    temp
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                subprocess.run([
                    "git", "-C", temp,
                    "sparse-checkout", "set", self.sparse_dir
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                if self.cleanup and os.path.exists(self.upstream_path):
                    shutil.rmtree(self.upstream_path)

                os.makedirs(os.path.dirname(self.upstream_path), exist_ok=True)
                shutil.move(os.path.join(temp, self.sparse_dir), self.upstream_path)

                init_file = os.path.join(self.upstream_path, "__init__.py")
                open(init_file, "a").close()

            logger.info("Regexes updated successfully.")

        except subprocess.CalledProcessError:
            logger.error("Git operation failed.")
        except (OSError, IOError):
            logger.error("File system error during update.")
        except Exception:
            logger.exception("Unexpected error during update.")
