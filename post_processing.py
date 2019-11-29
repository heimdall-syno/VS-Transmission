import os, sys, fnmatch, argparse, subprocess
from subprocess import Popen, PIPE, STDOUT, call
from shutil import copy, copyfile

## Add modules from the submodule (vs-utils)
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "VS-Utils"))
from mediainfo import ffprobe_file
from parse import parse_cfg

## Parse the config
config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.txt'
cfg = parse_cfg(config_file, "client")

synoclient_path = "/data/vs-transmission/VS-Utils/daemon/client.py"

#####################################################################
###                    File system functions                      ###
#####################################################################

def files_find_ext(path, ext):
	''' Find all files in the given path with the extension. '''

	ext_files = []
	for root, _, filenames in os.walk(path):
		for filename in fnmatch.filter(filenames, "*.%s" % ext):
			if ("sample" not in filename):
				ext_files.append(os.path.join(root, filename))
	return ext_files

def file_copy(src, dst, args):
	''' Copy file to directory and change owner. '''

	## Without renaming the file
	file_name = os.path.basename(src)
	new_file_path = os.path.join(dst, file_name)
	if not os.path.exists(new_file_path):
		copy(src, dst)
		os.chown(new_file_path, args.userid, args.groupid)
		return dst

	return 0

def file_copy_args(dst, args):
	''' Copy file to directory and change owner. '''

	## Copy the video file to the specified destination
	new_file = file_copy(args.directory, dst, args)
	if not new_file:
		print("Error: Could not copy file (%s) to destination (%s)" % (args.directory, dst))
		return 0

	return new_file

def directory_create_owner(args):
	''' Create a directory by the file name and change owner. '''

	dir_name = ".".join(args.name.split(".")[:-1])
	new_dir_path = os.path.join(args.directory, dir_name)
	if not os.path.exists(new_dir_path):
		os.mkdir(new_dir_path)
		os.chown(new_dir_path, args.userid, args.groupid)
	return new_dir_path

#####################################################################
###                      Synology functions                       ###
#####################################################################

def syno_add_file(file_path, synoclient_path):
	''' Add a file to the SynoIndex via webserver. '''

	process = subprocess.Popen(["python", synoclient_path, "-o", "a", "-f", file_path],
							   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	if(stderr): print(stderr)
	if(stdout): print(stdout)

#####################################################################
###                      Handbrake functions                      ###
#####################################################################

def copy_file_to_handbrake(src, args):
	''' Copy file to the handbrake watch directory and change owner. '''

	## Get all media info about the file
	codec = ffprobe_file(src)["video_codec"]

	## Check whether it is x264 based
	if codec != "h264" and codec != "x264":
		return 0

	## Copy the video file to the handbrake watch directory
	watch_dir = os.path.join(cfg.handbrake, "watch")
	new_file = file_copy(src, watch_dir, args)
	if not new_file:
		print("Error: Could not copy file (%s) to handbrake watch directory" % (src))
		return 0
	print("Copied file (%s) to handbrake watch directory" % (src))

	## Create convert-file to note the original path
	file_name = "%s.txt" % (".".join(os.path.basename(src).split(".")[:-1]))
	convert_file = os.path.join(cfg.handbrake, "convert", file_name)
	with open(convert_file, 'w+') as f: f.write('%s' % src)
	print("Create convert file (%s)" % (convert_file))

	return new_file

def post_processing(args):
	''' Post processing '''

	## If torrent is a single file create a directory and copy that file
	abs_path = os.path.join(args.directory, args.name)
	if os.path.isfile(abs_path):
		new_dir = directory_create_owner(args)
		abs_path = file_copy_args(new_dir, args)

	## If there are RAR files extract them into the top directory
	rar_files = files_find_ext(abs_path, "rar")
	print("Found some rar files: " + ", ".join(rar_files))
	for rar_file in rar_files:
		print("rar file \"%s\", try to unrar it" % (rar_file))
		process = Popen(["unrar", "x", "-o+", rar_file, abs_path], stdout=PIPE, stderr=PIPE)
		stdout, stderr = process.communicate()
		print(stderr)

	## Import all non-compressed video files
	video_files = [files_find_ext(abs_path, ext) for ext in ["mkv", "mp4"]]
	video_files = [i for sl in video_files for i in sl]
	for video in video_files:
		syno_add_file(video, synoclient_path)

	## If the video file is x264-based copy it to the watch directory of the handbrake
	## docker container
	if (args.handbrake):
		for video in video_files:
			copy_file_to_handbrake(video, args)

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
