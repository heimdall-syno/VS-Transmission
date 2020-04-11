#  VS-Transmission

VS-Transmission is an extension "docker-transmission-openvpn" container for adding video files (e.g. movies and series) directly to Synology's VideoStation from within the container (https://github.com/haugene/docker-transmission-openvpn).

It is the first part of an automated toolchain which download, convert, rename and relocate video files for Synology's VideoStation.

Check out the second part of the toolchain - VS-Handbrake (https://github.com/heimdall-syno/VS-Handbrake) - which performs the conversion and renaming.

## Overview of the VS-Components
```
             +---------------------------------------------------------------------------------+
             |                                  Synology DSM                                   |
             +---------------------------------------------------------------------------------+
             |                  +--------------------+  +-----------------+                    |
             |                  |       Docker       |  |      Docker     |                    |
             |                  |transmission.openVpn|  |     Handbrake   |                    |
             |                  +--------------------+  +-----------------+                    |
             | +------------+   | +---------------+  |  | +-------------+ |  +---------------+ |
             | |VS-SynoIndex|   | |VS-Transmission|  |  | | VS-Handbrake| |  |VS-Notification| |
             | |   (Task)   +---->+   (Script)    +------>+   (Script)  +--->+    (Task)     | |
             | +------------+   | +---------------+  |  | +-------------+ |  +---------------+ |
             |                  +--------------------+  +-----------------+                    |
             |                                                                                 |
             +---------------------------------------------------------------------------------+
```

Check out the other components:


VS-SynoIndex:      https://github.com/heimdall-syno/VS-SynoIndex

VS-Handbrake:      https://github.com/heimdall-syno/VS-Handbrake

VS-Notification:   https://github.com/heimdall-syno/VS-Notification

VS-Playlist-Share: https://github.com/heimdall-syno/VS-Playlist-Share

## Quick Start

1. Clone the repository inside the root directory of the transmission-openvpn docker container e.g. "/volume1/docker/transmission".

2. Configure the transmission-openvpn docker container as shown below (Container configuration). In the example configuration the transmission container is located at /docker/transmission and the handbrake container at /docker/handbrake. If the files should be converted by handbrake after the download finished then add an mount pointing to the root container directory.

3. Make sure the Triggered task (Control Panel > Task Scheduler) for the /dev/net/tun device is configured:
	```
    Task:       Docker-Transmission
    User:       root
    Command:    bash /volume1/docker/transmission/openvpn_scripts/TUN.sh
    ```

4. If the container is well configured, up and running then install all dependencies:
    ```
    $ sudo ./autogen.sh
    ```

5. Setup VS-SynoIndex as described in the corresponding README (Clone & Triggered Task).

6. Edit the port number of the Syno-Index server in `post_processing.sh` according to the parameter in the triggered task.

7. _Optional: Setup VS-Handbrake as described in the corresponding README._

8. _Optional: Setup VS-Notification as described in the corresponding README._

## Container configuration

Port settings:
```
Local port    | Container port
--------------+---------------
9091          | 9091
```

Volume settings:
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
```

Network settings:
```
Name     | Driver
---------+---------
bridge   | bridge
```


Environment settings:
```
Variable                                    Value                                       Fix or overwritten
------------------------------------------+--------------------------------------------+------------------
TRANSMISSION_INCOMPLETE_DIR               | /filme                                     | overwritten by GUI
TRANSMISSION_PEER_PORT                    | 54754                                      | overwritten random
TRANSMISSION_SCRIPT_TORRENT_DONE_FILENAME | /data/vs-transmission/post_processing.sh   | Fix
TRANSMISSION_HOME                         | /data/transmission-home                    | Fix
LOCAL_NETWORK                             | 192.168.178.0/24                           | Fix
OPENVPN_USERNAME                          | <username>                                 | Fix
OPENVPN_PASSWORD                          | <password>                                 | Fix
```
