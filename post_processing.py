import os, sys, fnmatch, argparse, subprocess

## Add modules from the submodule (vs-utils)
cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(cur_dir, "VS-Utils"))
sys.path.append(os.path.join(cur_dir, "VS-SynoIndex"))
from files import files_find_ext, file_copy, file_copy_args
from files import directory_create_owner, unrar_files
from parse import parse_cfg, parse_dockerpath
from mediainfo import ffprobe_file
from client import client

## Parse the config
config_file = os.path.join(cur_dir, "config.txt")
cfg = parse_cfg(config_file, "vs-transmission", "docker")

def write_convert_file(source, source_host, root_host, output_host):

	## Create convert file path
	convert_file = "%s.txt" % (".".join(os.path.basename(source).split(".")[:-1]))
	convert_file = os.path.join(cfg.handbrake, "convert", convert_file)

	## Write the convert file
	convert_content = "root_host:%s\nsource_host:%s\noutput_host:%s" % (root_host, source_host, output_host)
	with open(convert_file, 'w+') as f: f.write(convert_content)
	print("Created convert file (%s)" % (convert_file))

def copy_file_to_handbrake(args, source, source_host, root_host):
	''' Copy file to the handbrake watch directory and change owner. '''

	## Get all media info about the file
	codec = ffprobe_file(source)["video_codec"]

	## Check whether it is one codec of the config is present
	if codec not in cfg.codecs:
		return

	## Copy the video file to the handbrake watch directory
	watch_dir = os.path.join(cfg.handbrake, "watch")
	output = file_copy(source, watch_dir, args)
	output_host = parse_dockerpath(cfg.mapping, output)
	if not output:
		print("Error: Could not copy file (%s) to handbrake watch directory" % (source))
		return
	print("Copied file (%s) to handbrake watch directory" % (source))

	## Write the convert file with all necessary information
	write_convert_file(source, source_host, root_host, output_host)

def fix_single_file(args):
	""" If a single video file was downloaded create a directory and copy the file

	Arguments:
		args {Namespace} -- Namespace containing all shell arguments

	Returns:
		string -- Path of the copied file.
	"""

	abs_path = os.path.join(args.directory, args.name)
	if os.path.isfile(abs_path):
		new_dir = directory_create_owner(args)
		abs_path = file_copy_args(new_dir, args)
	return abs_path

def post_processing(args):
	''' Post processing '''

	## If torrent is a single file create a directory and copy that file
	abs_path = fix_single_file(args)

	## If there are RAR files extract them into the top directory
	unrar_files(abs_path)

	## Import all non-compressed video files
	source_files = [files_find_ext(abs_path, ext) for ext in ["mkv", "mp4"]]
	source_files = [i for sl in source_files for i in sl]
	for source in source_files:
		source_host = parse_dockerpath(cfg.mapping, source)
		client(source_host)

	## If the video file is x264-based copy it to the watch directory of the handbrake
	## docker container
	if (args.handbrake):
		for source in source_files:
			(source_host, root_host) = parse_dockerpath(cfg.mapping, source)
			copy_file_to_handbrake(args, source, source_host, root_host)

def main():

	## Parse the shell arguments
	args = argparse.Namespace()
	parser = argparse.ArgumentParser(description='Post Processing of torrents via transmission')
	parser.add_argument('-n','--name', help='Name of the torrent', required=True)
	parser.add_argument('-d','--directory', help='Directory of the torrent', required=True)
	parser.add_argument('-u','--userid', help='ID of the user (PUID)', type=int, required=True)
	parser.add_argument('-g','--groupid', help='ID of the group (PGID)', type=int, required=True)
	parser.add_argument('-b','--handbrake', help='Pipe to handbrake', action='store_true', required=False)
	args = parser.parse_args()

	## Post Processing
	post_processing(args)

if __name__ == "__main__":
	main()
