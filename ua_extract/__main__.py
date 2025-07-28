#!/usr/bin/env python3
"""
UA-Extract CLI tool for updating regex and fixture files from an upstream source.

This script provides a command-line interface to fetch and update regex and fixture files
from a specified Git repository (default: matomo-org/device-detector) using
either Git cloning or GitHub API methods. It supports sparse checkouts and
optional cleanup of existing files.
"""

import argparse
import sys
from pathlib import Path
from .update_regex import Regexes, UpdateMethod

ROOT_PATH = Path(__file__).parent.resolve()


def message_callback(message: str):
    """Callback function to print progress messages."""
    print(message, file=sys.stderr)


def main():
    """
    Main function to handle command-line arguments and execute the appropriate command.

    Supports two commands:
    - update_regexes: Updates regex and fixture files from an upstream source.
    - help: Displays help for all commands or a specific command.

    Exits with appropriate status codes on errors.
    """

    parser = argparse.ArgumentParser(
        prog="ua_extract",
        description="UA-Extract CLI for updating regex and fixture files from an upstream source",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    update_parser = subparsers.add_parser(
        "update_regexes",
        help="Update regex and fixture files from upstream source",
        description="Update regex and fixture files from upstream source"
    )

    update_parser.add_argument(
        "-p",
        "--path",
        default=ROOT_PATH / "regexes" / "upstream",
        type=Path,
        help="Destination path for regex files"
    )

    update_parser.add_argument(
        "-r",
        "--repo",
        default="https://github.com/matomo-org/device-detector.git",
        help="Git repository URL"
    )

    update_parser.add_argument(
        "-b",
        "--branch",
        default="master",
        help="Git branch name"
    )

    update_parser.add_argument(
        "-d",
        "--dir",
        default="regexes",
        help="Sparse directory in the repository for regex files"
    )

    update_parser.add_argument(
        "--fixtures-dir",
        default="Tests/fixtures",
        help="Sparse directory in the repository for general fixtures"
    )

    update_parser.add_argument(
        "--fixtures-path",
        default=ROOT_PATH / "tests" / "fixtures" / "upstream",
        type=Path,
        help="Destination path for general fixture files"
    )

    update_parser.add_argument(
        "--client-dir",
        default="Tests/Parser/Client/fixtures",
        help="Sparse directory in the repository for client fixtures"
    )

    update_parser.add_argument(
        "--client-path",
        default=ROOT_PATH / "tests" / "parser" / "fixtures" / "upstream" / "client",
        type=Path,
        help="Destination path for client fixture files"
    )

    update_parser.add_argument(
        "--device-dir",
        default="Tests/Parser/Device/fixtures",
        help="Sparse directory in the repository for device fixtures"
    )

    update_parser.add_argument(
        "--device-path",
        default=ROOT_PATH / "tests" / "parser" / "fixtures" / "upstream" / "device",
        type=Path,
        help="Destination path for device fixture files"
    )

    update_parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="Delete existing regex and fixture files before updating"
    )

    update_parser.add_argument(
        "-m",
        "--method",
        choices=[method.value for method in UpdateMethod],
        default="git",
        help="Update method: 'git' (clone via Git) or 'api' (download via GitHub API)"
    )

    update_parser.add_argument(
        "-g",
        "--github-token",
        default=None,
        help="GitHub personal access token for API method (default: from GITHUB_TOKEN env var)"
    )

    help_parser = subparsers.add_parser(
        "help",
        help="Show detailed help for all available commands",
        description="Show detailed help for all available commands"
    )

    help_parser.add_argument(
        "command_name",
        nargs="?",
        help="Optional: specify a command to show its detailed help (e.g., 'update_regexes')"
    )

    args = parser.parse_args()

    if args.command == "help":
        if args.command_name:
            command = subparsers._name_parser_map.get(args.command_name)
            if command:
                command.print_help()
            else:
                print(f"Error: Unknown command '{args.command_name}'", file=sys.stderr)
                parser.print_help()
                sys.exit(1)
        else:
            print("Available commands:")
            for name, subparser in subparsers._name_parser_map.items():
                print(f"  {name}: {subparser.description or 'No description available'}")
            print("\nUse 'ua_extract <command> --help' for detailed help on a specific command.")
            sys.exit(0)

    elif args.command == "update_regexes":
        try:
            for path in [args.path, args.fixtures_path, args.client_path, args.device_path]:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                elif not path.is_dir():
                    print(f"Error: '{path}' is not a directory", file=sys.stderr)
                    sys.exit(1)

        except PermissionError as e:
            print(f"Error: No permission to create or access path: {e}", file=sys.stderr)
            sys.exit(1)

        if not args.repo.startswith(("https://", "http://", "git@")):
            print(f"Error: Invalid repository URL '{args.repo}'", file=sys.stderr)
            sys.exit(1)

        try:
            regexes = Regexes(
                upstream_path=str(args.path),
                repo_url=args.repo,
                branch=args.branch,
                sparse_dir=args.dir,
                sparse_fixtures_dir=args.fixtures_dir,
                fixtures_upstream_path=str(args.fixtures_path),
                sparse_client_dir=args.client_dir,
                client_upstream_dir=str(args.client_path),
                sparse_device_dir=args.device_dir,
                device_upstream_dir=str(args.device_path),
                cleanup=args.cleanup,
                github_token=args.github_token,
                message_callback=message_callback
            )
            regexes.update_regexes(method=args.method)
            print(f"Successfully updated regex and fixture files")

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(2)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()