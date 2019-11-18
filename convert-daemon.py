import os, time, logging, argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from server import server
from parse import parse_cfg
from mediainfo import ffprobe_file
from namingseries import naming_episode, get_original_path

season_types = ["Serien", "Dokus", "Anime"]

## Parse the config
config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.txt'
cfg = parse_cfg(config_file, "server")

## Setup the logging files
server_log = "%s/%s" % (cfg.server_logs, "convert_daemon.log")
if not os.path.isfile(server_log): open(server_log, 'a').close()

## Setup the logging format
logging.basicConfig(filename=server_log, filemode='a',
					format='%(asctime)s - %(levelname)s: %(message)s')

stats = {}

class HandbrakeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        modify_path = event.src_path
        if os.path.isfile(modify_path):

            print(ffprobe_file(modify_path))

            ## Get the duration as indicator if the file is complete
            duration = ffprobe_file(modify_path)["duration"]

            ## If it is not in the stats add it
            if modify_path not in stats:
                stats[modify_path] = (duration, False)

            ## If it is already in the stats and finished then start the naming process
            ## otherwise update the duration
            elif (stats.get(modify_path) == "N/A" and duration != "N/A"):
                stats[modify_path] = (duration, True)
                convert_finished(modify_path)
        print(stats)

def convert_finished(path):

    print("End of convertion for file: %s" %(path))
    convert = "%s.txt" % os.path.splitext(path)[0].replace("/output/", "/convert/")
    get_original_path(convert)

    if any(season_type in convert for season_type in season_types):
        args = argparse.Namespace(file=path, convert=convert)
        print("HIER")
        #naming_episode(args)

def main():
    event_handler = HandbrakeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=cfg.handbrake_output, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()