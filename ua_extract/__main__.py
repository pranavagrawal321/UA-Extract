#!/usr/bin/env python3
"""
UA-Extract CLI tool for updating regex files from an upstream source.

This script provides a command-line interface to fetch and update regex files
from a specified Git repository (default: matomo-org/device-detector) using
either Git cloning or GitHub API methods. It supports sparse checkouts and
optional cleanup of existing files.
"""

import argparse
import sys
import os
from pathlib import Path
from .update_regex import Regexes, UpdateMethod

ROOT_PATH = Path(__file__).parent.resolve()


def main():
    """
    Main function to handle command-line arguments and execute the appropriate command.

    Supports two commands:
    - update_regexes: Updates regex files from an upstream source.
    - help: Displays help for all commands or a specific command.

    Exits with appropriate status codes on errors.
    """

    parser = argparse.ArgumentParser(
        prog="ua_extract",
        description="UA-Extract CLI for updating regex files from an upstream source",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    update_parser = subparsers.add_parser(
        "update_regexes",
        help="Update regex files from upstream source",
        description="Update regex files from upstream source"
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
        help="Sparse directory in the repository to fetch"
    )

    update_parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="Delete existing regex files before updating"
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
        default=os.getenv("GITHUB_TOKEN"),
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
            if not args.path.exists():
                args.path.mkdir(parents=True, exist_ok=True)

            elif not args.path.is_dir():
                print(f"Error: '{args.path}' is not a directory", file=sys.stderr)
                sys.exit(1)

        except PermissionError:
            print(f"Error: No permission to create or access '{args.path}'", file=sys.stderr)
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
                cleanup=args.cleanup,
                github_token=args.github_token
            )
            regexes.update_regexes(method=args.method)
            print(f"Successfully updated regex files in '{args.path}'")

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