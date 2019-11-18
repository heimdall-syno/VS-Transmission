import sys, glob, os, cv2, re, warnings, csv, argparse
from distutils.util import strtobool
from shutil import move
from collections import Counter
from argparse import Namespace

def get_resolution(res):

	## Round the real resolution of the video file
	## to the common resolution
	if (res == 0): return -1
	if (0 < res and res <= 360): return "360p"
	elif (360 < res and res <= 480): return "480p"
	elif (480 < res and res <= 720): return "720p"
	elif (720 < res and res <= 1080): return "1080p"
	elif (1080 < res and res <= 2160): return "2160p"
	else: return -1

def analyze_series(series):

	## Get all file names inside the season
	path = series.path
	files = sorted([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])

	## Get the series name for the files
	if (series.original):
		directories = series.original.split(os.sep)
		series.name = directories[directories.index(series.series_path) + 1].replace(" ", "-")
		series.original = "%s/" % os.sep.join(directories[:(directories.index(series.series_path) + 3)])
	else:
		series.name = path.split(os.sep)[-2].replace(" ", "-")

	## Analyze the extensions of the season
	extensions = Counter([f.split(".")[-1] for f in files]).most_common()
	extensions = [ext for ext in extensions if ext[0] != "vsmeta" and ext[0] != "srt"]
	if (len(extensions) < 1):
		print("No valid extension found in the folder")
		exit()
	series.extension = extensions[0][0]

	## Analyze resolution of the season
	test_vid = [path + os.sep + f for f in files if f.split(".")[-1] != "vsmeta" and
												  f.split(".")[-1] != "srt"][0]
	video = cv2.VideoCapture(test_vid)
	height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
	if not series.original:
		print()
	series.resolution = get_resolution(height)
	if(series.resolution == -1):
		print("The resolution of the first episode of the series was invalid")
		exit()

	## Analyze the current season number
	try:
		series.season = [f for f in files[0].split(".") if "s0" in f.lower()][0]
		series.season = "S{}".format(re.split('s|e', series.season.lower())[1])
		series.token = [i for i,f in enumerate(files[0].split(".")) if "s0" in f.lower()][0]
	except IndexError:
		series.season = "S01"
		match = re.search('\d\d', files[0], flags=0).group()
		series.token = [i for i, m in enumerate(files[0].split(".")) if match in m][0]

	if not hasattr(series, 'token'):
		print("The episode information could not be found in the files")
		exit()
	return series

def get_season_ep(series, filePath):

	old_episode = filePath.split("\\")[-1]
	if (series.mode == "auto" and len(old_episode.split(".")) <= 2):
		print("Error: The file {} seems to be corrupt in filename format".format(old_episode))
		print("Info: Please choose another mode to fix it")
		input("")
		exit()
	token = old_episode.split(".")[series.token]
	return (old_episode, token)

def get_new_episodes(series):

	file_list = []
	incr_iter = series.incr_iter - 1
	## iterate over all subfolders
	for folder, subfolders, files in os.walk(series.path):
		for i, file in enumerate(sorted(files)):
			filePath = os.path.join(os.path.abspath(folder), file)
			if (series.extension not in filePath) and ("srt" not in filePath):
				continue

			## Get the current season and episode
			(old_episode, token) =  get_season_ep(series, filePath)

			## Auto Mode = s01e01 -> S01E01
			if(series.mode == "auto"):
				series.season = filePath.split(os.sep)
				series.season = [s.split()[1] for s in series.season if "Staffel" in s][0]
				series.season = "S{}".format(series.season)
				try:
					series.episode = re.search('(e|E)\d\d(\d)?', token, flags=0).group().replace("e", "E")
				except AttributeError:
					series.episode = re.search('\d\d?', token, flags=0).group()

			## Increment Mode S02E01,S02E02, ..
			elif (series.mode == "incr"):
				if ("vsmeta" not in old_episode and "srt" not in old_episode):
					incr_iter = incr_iter + 1
				series.season = filePath.split(os.sep)
				try:
					series.season = [s.split()[1] for s in series.season if "Staffel" in s][0]
				except:
					print("Error: Foldername does not contain \"Staffel\" as expected!")
					exit()
				series.season = "S{}".format(series.season)
				if(len(files) > 99):
					series.episode = "E{:03d}".format(incr_iter)
				else:
					series.episode = "E{:02d}".format(incr_iter)

			## Dict mode
			else:
				try:
					series.episode = re.search('(e|E)\d\d(\d)?', token, flags=0).group().replace("e", "E")
				except AttributeError:
					series.episode = re.search('\d\d?', token, flags=0).group()

				episode_nr = series.episode.replace("E","")
				if (series.dict.get(episode_nr, None) == None):
					##for key, value in series.dict.items():
					##	print ("{} -> {}".format(key, value))
					print("Episode {} not found ({}), skip it".format(filePath, episode_nr))
					continue
				series.season, series.episode = series.dict.get(episode_nr, None)
				series.season = "S{}".format(series.season)
				series.episode = "E{}".format(series.episode)

			## if it is a normal episode rename it normally, if not include the vsmeta
			extension = series.extension
			if ("vsmeta" in old_episode): extension = extension + ".vsmeta"
			elif ("srt" in old_episode): extension = "srt"
			new_episode = "{}.{}{}.{}.{}".format(series.name, series.season, series.episode,
												 series.resolution, extension)
			new_path = "\\".join(filePath.split("\\")[:-1]) + "\\" + new_episode
			file_list.append((filePath, new_path))

	series.episodes = file_list

def rename_episodes(series):

	## Renaming
	for (old_episode, new_episode) in series.episodes:
		os.rename(old_episode, new_episode)
	print("... Finished renaming")

def print_episodes(series):

	## Print episode filenames
	for (old_episode, new_episode) in series.episodes:
		print("Old episode name: {}".format(old_episode))
		print("New episode name: {}\n".format(new_episode))

	answer = input("Are you sure to rename the above episodes? [Y|N]: ")
	if not strtobool(answer):
		print("... Finished")
		exit()

def parse_dict_file(series):

	## Check the mode
	if (series.mode != "dict"):
		return 0

	## Read in matching dict
	matching_dict = {}
	with open(series.dict_path) as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')
		for row in readCSV:
			start, end = [int(x) for x in row[0].split("-")]
			for x in range(start, end + 1):
				digit_fmt = "{:03d}" if end - start > 99 else "{:02d}"
				matching_dict["{:03d}".format(x)] = (row[1].replace("Staffel", "").replace(" ",""), digit_fmt.format((x - start + 1)))

	return matching_dict

def gui_mode():

	while (1):

		## Check arguments
		if (len(sys.argv) < 2):
			mode, dict_path = ("" for _ in range(2))

			## Validate mode
			while (mode != "auto" and mode != "incr" and mode != "dict"):
				mode = input("Choose a mode which should be executed [ Auto | incr | dict ]: ") or "auto"

			## increment mode
			incr_iter = 0
			if (mode == "incr"):
				incr_iter = int(input("Number of the first episode [1]: ") or "1")
				if (incr_iter < 1):
					print("Invalid first episode")
					exit()
			## dict mode
			if (mode == "dict"):
				dict_path = input("Drop the dict as csv file here: ").replace("\"", "")

			path = input("Drop the series season folder here: ").replace("\"", "")
		else: path = sys.argv[1]
		if not os.path.exists(path):
			print("The passed folder doesn't exist")
			exit()

		## Create a namespace for passing between functions
		series = Namespace(path = path, mode=mode, incr_iter=incr_iter, dict_path=dict_path)
		series = analyze_series(series)

		## Parse dict file if needed
		series.dict = parse_dict_file(series)

		## Rename_episodes
		get_new_episodes(series)

		## Print the new episode names to check if they're valid
		print_episodes(series)

		## Rename the episodes
		rename_episodes(series)

		print()

def daemon_mode(args):

	from parse import parse_cfg
	config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.txt'
	cfg = parse_cfg(config_file, "server")

	## Get the original path of the video file on the host system
	with open(args.convert, "r") as f: original_path = f.readlines()[0]
	map = [m for m in cfg.mapping if original_path.split(os.sep)[1] in m[0]][0]
	original_path = original_path.replace(map[0], map[1])

	## Get the name of the root series directory
	series_path = map[1].split(os.sep)[-1]

	## Get all information about the episode and season
	path = os.path.abspath(os.path.join(args.file, os.pardir))
	series = Namespace(file=args.file, path=path, mode="auto", incr_iter=None,
					   dict_path=None, original=original_path, series_path=series_path)
	series = analyze_series(series)
	series.episode = get_season_ep(series, series.file)[1]

	## Clean up the namespace
	for attr in ['incr_iter', 'dict_path', 'mode', 'season', 'token']:
		delattr(series, attr)

	## Move the file back to the original path
	file_name = "%s.%s.%s.%s" % (series.name, series.episode, series.resolution, series.extension)
	file_dst = os.path.join(series.original, file_name)
	move(series.file, file_dst)

	## Delete the corresponding convert file
	os.remove(args.convert)

def main():

	## Parse the shell arguments
	args = argparse.Namespace()
	parser = argparse.ArgumentParser(description='Series naming script')
	parser.add_argument('-d','--daemon', help='Daemon mode', action='store_true', required=False)
	parser.add_argument('-f','--file', help='Path to the video file', required=False)
	parser.add_argument('-c','--convert', help='Path to the convert file', required=False)
	args = parser.parse_args()
	if (args.daemon):
		daemon_mode(args)
	else:
		gui_mode()

if __name__ == "__main__":
	main()