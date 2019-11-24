import sys, glob, os, cv2, re, warnings, csv, argparse, json
from distutils.util import strtobool
from shutil import move
from collections import Counter
from argparse import Namespace

from parse import parse_cfg

season_desc = "Staffel"

config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.txt'
cfg = parse_cfg(config_file, "server")

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

	## Get the extensions of the season
	series.extension = os.path.splitext(series.file)[1]

	## Analyze resolution of the season
	video = cv2.VideoCapture(series.file)
	height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
	series.resolution = get_resolution(height)
	if(series.resolution == -1):
		print("The resolution of the series episode was invalid")
		exit()

	## Analyze the current season number
	splitted = series.file.split(series.delim)
	season_ep = [f for f in splitted if "s0" in f.lower() or "s1" in f.lower()][0]
	series.season = "{}".format(re.split('s|e', season_ep.lower())[1])
	series.episode = "S%sE%s" % (series.season, re.split('s|e', season_ep.lower())[2])
	series.season = "%s %s" % (season_desc, series.season)

	## Get the series name of the file
	directories = series.original.split(os.sep)
	series.name = directories[directories.index(series.series_path) + 1].replace(" ", "-")

	## Get the destination directory
	series.dst = "%s/" % os.sep.join(directories[:(directories.index(series.series_path) + 3)])
	if season_desc not in series.dst.split(os.sep)[-1]:
		series.dst = directories[:(directories.index(series.series_path) + 2)] + [series.season]
		series.dst = "%s%s" % (os.sep,os.path.join(*series.dst))
		if not os.path.isdir(series.dst):
			os.mkdir(series.dst)

	return series

def naming_episode(args):

	print("  Naming: Started")

	## Get the delimiter of the video filename
	delimiters = [".", "-", "_"]
	delimiter_count = Counter(args.file).most_common()
	delimiter_count = [(key, val) for key, val in delimiter_count if key in delimiters]
	delimiter = sorted(delimiter_count, key=lambda x: x[1])[-1][0]

	## Get the name of the root series directory
	series_path = args.original.split(os.sep)[2]

	## Get all information about the episode and season
	path = os.path.abspath(os.path.join(args.file, os.pardir))
	series = Namespace(file=args.file, path=path, delim=delimiter, original=args.original, series_path=series_path)
	series = analyze_series(series)
	print("  Analysis Namespace: %s" % series)

	## Move the file back to the original path
	file_name = "%s.%s.%s%s" % (series.name, series.episode, series.resolution, series.extension)
	file_dst = os.path.join(series.dst, file_name)
	print("  Moving file: %s" % file_dst)
	move(series.file, file_dst)
	return file_dst

if __name__ == "__main__":

	args = argparse.Namespace()
	parser = argparse.ArgumentParser(description='Series naming script')
	parser.add_argument('-f','--file', help='Path to the video file', required=True)
	parser.add_argument('-c','--convert', help='Path to the convert file', required=True)
	args = parser.parse_args()
	naming_episode(args)