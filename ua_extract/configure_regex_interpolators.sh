#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$SCRIPT_DIR/regexes"

if [[ ! -d "$BASE_DIR" ]]; then
    echo "Error: $BASE_DIR does not exist"
    exit 1
fi

# BSD sed (macOS) requires a backup suffix argument for -i.
# GNU sed (Linux) does not.
if [[ "$OSTYPE" == darwin* ]]; then
    SED_INPLACE=(-i '')
else
    SED_INPLACE=(-i)
fi

find "$BASE_DIR" -type f -name "*.yml" \
    -exec sed "${SED_INPLACE[@]}" -E \
        -e 's/\$([1-5])/\\g<\1>/g' \
        -e "s/eZee'Tab\\\\g/eZee'Tab\\\\\\\\g/g" \
        -e "s/(['\"])#/\1 #/g" \
        {} +