#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Source our persisted env variables from container startup
if [[ $(cat /proc/1/cgroup | grep docker) ]]; then
    . /etc/transmission/environment-variables.sh
    python3 "$DIR/post_processing.py" -d "$TR_TORRENT_DIR" -n "$TR_TORRENT_NAME" -u "$PUID" -g "$PGID"
else
    python3 "$DIR/post_processing.py" -d "$TR_TORRENT_DIR" -n "$TR_TORRENT_NAME"
fi
