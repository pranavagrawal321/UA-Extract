#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR/regexes"

find "$BASE_DIR" -name "*.yml" -type f -exec sed -i -E 's/\$([1-5])/\\g<\1>/g' {} +
find "$BASE_DIR" -name "*.yml" -type f -exec sed -i "s/eZee'Tab\\\\g/eZee'Tab\\\\\\\\g/g" {} +