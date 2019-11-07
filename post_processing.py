import os, fnmatch, argparse, subprocess, logging, sys, shlex, re
from subprocess import Popen, PIPE, STDOUT, call
from shutil import copy, copyfile

from mediainfo import ffprobe_file
from parse import parse_cfg

## Parse the config
config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.txt'
cfg = parse_cfg(config_file, "client")

## Setup the client logging file
client_log = "%s/%s" % (cfg.client_logs, "client.log")
logging.basicConfig(filename=client_log, filemode='a',
					format='%(asctime)s - %(levelname)s: %(message)s')

## Set the logger and its level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

allowed_ext = ["mkv", "mp4"]
synoclient_path = "/data/synoindex_scripts/client.py"

def find_files_with_extension(path, ext):
	''' Find all files in the given path with the extension. '''

	ext_files = []
	for root, _, filenames in os.walk(path):
		for filename in fnmatch.filter(filenames, "*.%s" % ext):
			if ("sample" not in filename):
				ext_files.append(os.path.join(root, filename))
	return ext_files

def add_file_to_syno(file_path, synoclient_path):
	''' Add a file to the SynoIndex via webserver. '''

	process = subprocess.Popen(["python", synoclient_path, "-o", "a", "-f", file_path],
							   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	if(stderr): print(stderr)
	if(stdout): print(stdout)

def create_dir_owner(args):
	''' Create a directory by the file name and change owner. '''

	dir_name = ".".join(args.name.split(".")[:-1])
	new_dir_path = os.path.join(args.directory, dir_name)
	if not os.path.exists(new_dir_path):
		os.mkdir(new_dir_path)
		os.chown(new_dir_path, args.userid, args.groupid)
	return new_dir_path

def copy_file(src, dst, name, args):
	''' Copy file to directory and change owner. '''

	## Without renaming the file
	file_name = os.path.basename(src)
	new_file_path = os.path.join(dst, file_name)
	if not name and not os.path.exists(new_file_path):
		copy(src, dst)
		os.chown(new_file_path, args.userid, args.groupid)
		return dst

	## Copy and rename the file
	dst_name = os.path.join(dst, name)
	if name and not os.path.exists(dst_name):
		copyfile(src, dst_name)
		os.chown(dst_name, args.userid, args.groupid)
		return dst

	return 0

def copy_file_args(dst, args):
	''' Copy file to directory and change owner. '''

	## Copy the video file to the specified destination
	new_file = copy_file(args.directory, dst, 0, args)
	if not new_file:
		logging.error("Could not copy file (%s) to destination (%s)" % (args.directory, dst))
		return 0

	return new_file

def copy_file_to_handbrake(src, args):
	''' Copy file to the handbrake watch directory and change owner. '''

	## Get all media info about the file
	info = ffprobe_file(src)
	codec = info["video_codec"]

	## Check whether it is x264 based
	if codec != "h264" and codec != "x264":
		return 0

	## Copy the video file to the handbrake watch directory
	src_dir = src.split(os.sep)[-2]
	dst_name = "%s%s" % (src_dir, os.path.splitext(src)[1])
	new_file = copy_file(src, cfg.handbrake, dst_name, args)
	if not new_file:
		logging.error("Could not copy file (%s) to handbrake watch directory" % (src))
		return 0
	logger.debug("Copied file (%s) to handbrake watch directory" % (src))

	return new_file

def post_processing(args):
	''' Post processing '''

	## If torrent is a single file create a directory and copy that file
	abs_path = os.path.join(args.directory, args.name)
	if os.path.isfile(abs_path):
		new_dir = create_dir_owner(args)
		abs_path = copy_file_args(new_dir, args)

	## If there are RAR files extract them into the top directory
	rar_files = find_files_with_extension(abs_path, "rar")
	logger.debug("Found some rar files: " + ", ".join(rar_files))
	for rar_file in rar_files:
		logger.debug("rar file \"%s\", try to unrar it" % (rar_file))
		process = Popen(["unrar", "x", "-o+", rar_file, abs_path], stdout=PIPE, stderr=PIPE)
		stdout, stderr = process.communicate()
		logger.debug(stderr)

	## Import all non-compressed video files
	video_files = [find_files_with_extension(abs_path, ext) for ext in allowed_ext]
	video_files = [i for sl in video_files for i in sl]
	for video in video_files:
		add_file_to_syno(video, synoclient_path)

	## If the video file is x264-based copy it to the watch directory of the handbrake
	## docker container
	for video in video_files:
		copy_file_to_handbrake(video, args)

def main():
	args = argparse.Namespace()
	parser = argparse.ArgumentParser(description='Post Processing of torrents via transmission')
	parser.add_argument('-n','--name', help='Name of the torrent', required=True)
	parser.add_argument('-d','--directory', help='Directory of the torrent', required=True)
	parser.add_argument('-u','--userid', help='ID of the user (PUID)', type=int, required=True)
	parser.add_argument('-g','--groupid', help='ID of the group (PGID)', type=int, required=True)
	args = parser.parse_args()

	## Post Processing
	post_processing(args)

if __name__ == "__main__":
	main()
