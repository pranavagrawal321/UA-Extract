import warnings
import sys


def enable_colored_warnings(color: str = "\033[33m"):
    reset = "\033[0m"

    def showwarning(
        message,
        category,
        filename,
        lineno,
        file=None,
        line=None,
    ):
        stream = file if file is not None else sys.stderr
        stream.write(f"{color}{filename}:{lineno}: {category.__name__}: {message}{reset}\n")

    warnings.showwarning = showwarning
