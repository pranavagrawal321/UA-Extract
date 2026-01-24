#!/bin/bash

BASE_DIR="ua_extract/regexes"
find "$BASE_DIR" -name "*.yml" -type f -print0 | xargs -0 sed -i -E 's/\$([1-5])/\\g<\1>/g'
find "$BASE_DIR" -name "*.yml" -type f -print0 | xargs -0 sed -i "s/eZee'Tab\\\\g/eZee'Tab\\\\\\\\g/g"