import os, time, argparse
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from server import server
from parse import parse_cfg
from namingseries import naming_episode

## Parse the config
config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.txt'
cfg = parse_cfg(config_file, "server")

def get_original_path(convert):
	try:
		with open(convert, "r") as f: original_path = f.readlines()[0]
		map = [m for m in cfg.mapping if original_path.split(os.sep)[1] in m[0]][0]
		original_path = original_path.replace(map[0], map[1])
	except IOError as e:
		print("Convert file does not exist")
		return -1
	return original_path

class HandbrakeHandler(FileSystemEventHandler):

    def on_deleted(self, event):

        ## Check whether handbrake deleted the temporary directory
        if os.path.splitext(event.src_path)[1] == '':
            output_dir = os.path.dirname(event.src_path)
            print("[%s] Handbrake finished converting files:" % datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M"))
            new_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if
                         os.path.isfile(os.path.join(output_dir, f))]

            ## Handle the naming of the converted file
            for new_file in new_files:
                print("  Name: %s" %(new_file))

                ## Check for the source file, continue if convert file doesnt exist
                convert = "%s.txt" % os.path.splitext(new_file)[0].replace("/output/", "/convert/").replace("/test/", "/convert/")
                original = get_original_path(convert)
                if (original == -1):
                    continue

                ## Check whether the file is a series based file
                if any(season_type in original.split(os.sep)[2] for season_type in cfg.handbrake_series):
                    print("  Type: Series-based")
                    args = argparse.Namespace(file=new_file, original=original)
                    file_dst = naming_episode(args)
                    if file_dst:
                        ## Delete the corresponding convert file
                        print("Delete convert file at %s" % (convert))
                        os.remove(convert)

                        # Add to synoindex
                        server(cfg, "a", file_dst)


                ## Check whether the file is a movie based file
                elif any(movie_type in original.split(os.sep)[2] for movie_type in cfg.handbrake_movies):
                    print("  Type: Movie-based")
                    args = argparse.Namespace(file=new_file, original=original)
                    print("  NOT SUPPORTED RIGHT NOW")
                    #naming_movies(args)
                print("  -----------------")
            print("")
def main():

    ## initialize the observer on the output directory of handbrake
    event_handler = HandbrakeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=cfg.handbrake_output, recursive=False)
    observer.start()

    ## Check whether second whether handbrake changed something
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()