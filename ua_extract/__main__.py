import argparse
import sys
from .update_regex import Regexes


def main():
    parser = argparse.ArgumentParser(prog="ua_extract", description="ua_extract CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    update_parser = subparsers.add_parser("update_user_agents", help="Update regexes from upstream")
    update_parser.add_argument("--path", default="ua_extract/regexes/upstream", help="Destination path")
    update_parser.add_argument("--repo", default="https://github.com/matomo-org/device-detector.git", help="Git repo URL")
    update_parser.add_argument("--branch", default="master", help="Git branch name")
    update_parser.add_argument("--sparse-dir", default="regexes", help="Sparse directory inside repo")
    update_parser.add_argument("--no-cleanup", action="store_true", help="Skip deleting existing folder")

    args = parser.parse_args()

    if args.command == "update_user_agents":
        regexes = Regexes(
            upstream_path=args.path,
            repo_url=args.repo,
            branch=args.branch,
            sparse_dir=args.sparse_dir,
            cleanup=not args.no_cleanup
        )
        regexes.update_user_agents()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
