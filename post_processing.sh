#!/bin/bash

# Source our persisted env variables from container startup
. /etc/transmission/environment-variables.sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Execute the post processing via Python
python3 "$DIR/post_processing.py" -d "$TR_TORRENT_DIR" -n "$TR_TORRENT_NAME" -u "$PUID" -g "$PGID" -p 32699
