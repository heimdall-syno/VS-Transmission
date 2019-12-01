VS-Transmission
=========

VS-Transmission is a simple python tool for adding video files direct to the Synology VideoStation from transmission running inside the docker-transmission-openvpn (https://github.com/haugene/docker-transmission-openvpn).

The tool creates a simple client/server architecture between the hostsystem and the docker container. Therefore the hostsystem runs a webservice (webservice.py) and listes on a specified port of the configuration file (config.txt). For every GET-Query (passing the current video file) the server (server.py) validates the input and executes the Synology onboard-script "synoindex". By doing so the passed file will be added to the general index of the synology system and to the media library of the VideoStation.

Inside the docker container runs transmission which downloads video files. The container must be configured to mount the necessary folders (download destinations and script-folder). After finishing the download transmission executes the post-processing script (must be set in the evironment variables). The post-processing script (post_processing.sh) executes the corresponding python script which checks whether the downloaded torrent is a video file or a folder containg a rar-zipped file. If there is a wellformed video file the client (client.py) invoke the URI of the webservices and passes the file-name.

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
TRANSMISSION_SCRIPT_TORRENT_DONE_FILENAME | /data/synoindex_scripts/post_processing.sh | Fix
TRANSMISSION_HOME                         | /data/transmission-home                    | Fix
LOCAL_NETWORK                             | 192.168.178.0/24                           | Fix
OPENVPN_USERNAME                          | <username>                                 | Fix
OPENVPN_PASSWORD                          | <password>                                 | Fix
```
------
#### Tool configuration

1. Make your changes to the config-file. For example:
	```
    [Mapping]
    /serien = /volume1/Serien
    /filme = /volume1/Filme
    /video = /volume1/video
    /dokus = /volume1/Dokus
    /tools = /volume1/Tools
    /anime = /volume1/Anime

    [Handbrake]
    handbrake = /docker/handbrake
    codecs = x264, h264
	```

2. Make sure that web.py module is supported by python:
    ```
    $ sudo pip install web-py
    ```

3. Create a task (task planer) for the webservice with the following settings:
	```
    Task:       SynoIndex-Webserver
    User:       <username> (not root)
    Command:    python /volume1/docker/transmission/synoindex_scripts/webservice.py
    ```
