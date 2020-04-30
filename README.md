#  VS-Transmission

VS-Transmission is a post-processing script for various download/torrent applications for Synology's DSM. It adds video files to the Synology index after the download finished in order to watch them instantly via media centers like VideoStation or Plex.

It is the first part of an automated toolchain (VS-Toolchain) which index, convert, rename and relocate (based on an uniform scheme) video files. The conversion, renaming and relocation is performed by the second part (VS-Handbrake). Optionally the toolchain can be extended to periodically notify all DSM users via mail about the new video files (VS-Notification) and automatically share new VideoStation playlists across all DSM users (VS-Playlist-Share).

## Overview of the VS-Toolchain
```
+---------------------------------------------------------------------------------------------------------+
|                                             Synology DSM                                                |
+---------------------------------------------------------------------------------------------------------+
|                                                                                    +-----------------+  |
|                                                                                    |      DSM        |  |
|  +--------------------+                                                            |VS-Playlist-Share|  |
|  |       Docker       +-------+                                                    |   (Optional)    |  |
|  |transmission openVpn|       |                                                    +-----------------+  |
|  +--------------------+       v                                                                         |
|            or            +----+------------+   +------------+   +--------------+    +---------------+   |
|  +--------------------+  |    DSM/Docker   +-->+   Docker   +-->+    Docker    +--->+     DSM       |   |
|  |        DSM         +--+ VS-Transmission |   |  Handbrake |   | VS-Handbrake |    |VS-Notification|   |
|  |    Transmission    |  |    (Required)   +-+ | (Optional) |   |  (Optional)  +--+ |  (Optional)   |   |
|  +--------------------+  +----+------------+ | +------------+   +--------------+  | +---------------+   |
|            or                 |              |                                    |                     |
|  +--------------------+       |              |                                    |                     |
|  |        DSM         +-------+              |                                    |                     |
|  |  Download-Station  |                      v                                    v                     |
|  +--------------------+    +-----------------+------------------------------------+------------------+  |
|                            |                                DSM Task                                 |  |
|                            |                              VS-SynoIndex                               |  |
|                            |                               (Required)                                |  |
|                            +-------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------------+
```

Check out the other components:


VS-SynoIndex:      https://github.com/heimdall-syno/VS-SynoIndex

VS-Handbrake:      https://github.com/heimdall-syno/VS-Handbrake

VS-Notification:   https://github.com/heimdall-syno/VS-Notification

VS-Playlist-Share: https://github.com/heimdall-syno/VS-Playlist-Share

## Dependencies (Packages)

- Python3
- ffmpeg

## DSM Transmission configuration

1. If Transmission runs directly in DSM then clone this repository into an arbitrary path.
    ```
    $ git clone https://github.com/heimdall-syno/VS-Transmission.git
    ```

2. Install all dependencies:
    ```
    $ curl https://bootstrap.pypa.io/get-pip.py -o /get-pip.py
    $ python3 /get-pip.py && rm -rf /get-pip.py
    $ export PATH=$PATH:/volume1/@appstore/py3k/usr/local/bin
    $ pip3 install -r requirements.txt
    ```

3. Setup VS-SynoIndex as described in the corresponding README (Clone & Triggered Task).

4. Configure VS-Transmission by editing config.txt as described in the corresponding description.

5. _Optional: Setup VS-Handbrake as described in the corresponding README and add a mount pointing to the root container directory._

6. _Optional: Setup VS-Notification as described in the corresponding README._

7. _Optional: Setup VS-Playlist-Share as described in the corresponding README._

## Docker configuration (transmission-openvpn)

1. If Transmission runs in a docker container then initially setup the docker container as described in the corresponding repository. The next steps refer to the docker container "docker-transmission-openvpn" which combine Transmission with a VPN connection (https://github.com/haugene/docker-transmission-openvpn).

3. After the container is well configured, up and running - clone this repository inside the root directory of the transmission-openvpn docker container e.g. "/volume1/docker/transmission".
    ```
    $ git clone https://github.com/heimdall-syno/VS-Transmission.git
    ```

4. Extend the container configuration by the settings shown below. In the example configuration the transmission container is located at /docker/transmission.

    - Volume settings:
      ```
      File/Folder                                       | Mount-Path            | Type
      --------------------------------------------------+-----------------------+-----
      docker/transmission/openvpn_scripts/resolv.conf   | /etc/resolv.conf      | rw
      docker/transmission                               | /data                 | rw
      Tools                                             | /tools                | rw
      Dokus                                             | /dokus                | rw
      video                                             | /video                | rw
      Filme                                             | /filme                | rw
      Serien                                            | /serien               | rw
      Anime                                             | /anime                | rw
      docker/handbrake                                  | /handbrake            | rw
      docker/logs                                       | /logs                 | rw
      ```

    - Environment settings:
      ```
      Variable                                    Value                                       Fix or overwritten
      ------------------------------------------+--------------------------------------------+------------------
      TRANSMISSION_INCOMPLETE_DIR               | /filme                                     | overwritten by GUI
      TRANSMISSION_PEER_PORT                    | 54754                                      | overwritten random
      TRANSMISSION_SCRIPT_TORRENT_DONE_FILENAME | /data/VS-Transmission/post_processing.sh   | Fix
      TRANSMISSION_HOME                         | /data/transmission-home                    | Fix
      LOCAL_NETWORK                             | 192.168.178.0/24                           | Fix
      OPENVPN_USERNAME                          | <username>                                 | Fix
      OPENVPN_PASSWORD                          | <password>                                 | Fix
      ```

5. Install all dependencies needed by the post processing script:
    ```
    $ cd VS-Transmission
    $ sudo ./autogen.sh
    ```

6. Setup VS-SynoIndex as described in the corresponding README (Clone & Triggered Task).

7. Configure VS-Transmission by editing the config.txt as described in the corresponding description.

8. _Optional: Setup VS-Handbrake as described in the corresponding README and add a mount pointing to the root container directory._

9. _Optional: Setup VS-Notification as described in the corresponding README._

10. _Optional: Setup VS-Playlist-Share as described in the corresponding README._
