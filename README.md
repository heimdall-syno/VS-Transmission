#  VS-Transmission

VS-Transmission enables adding video files (e.g. movies and series) directly to Synology's VideoStation from within the "docker-transmission-openvpn" container (https://github.com/haugene/docker-transmission-openvpn).

Optionally the files are converted by the handbrake docker container (https://github.com/jlesage/docker-handbrake).

## Quick Start

1. Configure the transmission-openvpn docker container as shown below (Container configuration). In the example configuration the transmission container is located at /docker/transmission and the handbrake container at /docker/handbrake. If the files should be converted by handbrake after the download finished then add an mount pointing to the root container directory.

2. Make sure the container is up and running. If so install all dependencies:
    ```
    $ sudo ./autogen.sh
    ```

3. Create a task (task planer) for the web-service with the following settings:
	```
    Task:       SynoIndex-Webserver
    User:       <username> (not root)
    Command:    python3 /volume1/docker/transmission/vs-transmission/VS-SynoIndex/webservice.py
    ```

4. If handbrake is enabled then make sure the docker container is up and running.

----
#### Container configuration

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
