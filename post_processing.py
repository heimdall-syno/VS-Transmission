import os, fnmatch, argparse, subprocess
from shutil import copy

allowed_ext = ["mkv", "mp4"]
synoclient_path = "/data/synoindex_scripts/client.py"

def files_with_ext(path, ext):
	''' Find all files in the given path with the extension. '''

	ext_files = []
	for root, dirnames, filenames in os.walk(path):
		for filename in fnmatch.filter(filenames, "*.%s" % ext):
			if ("sample" not in filename):
				ext_files.append(os.path.join(root, filename))
	return ext_files

def add_file_to_syno(file_path, synoclient_path):
	''' Add a file to the SynoIndex via webserver. '''

	print("Add to synoindex: %s" % file_path)
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

def copy_file(new_dir, args):
	''' Copy file to directory and change owner. '''
	
	abs_path = os.path.join(args.directory, args.name)
	new_file_path = os.path.join(new_dir, args.name)
	if not os.path.exists(new_file_path):
		copy(abs_path, new_dir)
		os.chown(new_file_path, args.userid, args.groupid)
	return new_dir
	
def post_processing(args):
	''' Post processing '''

	## Get the absolute path
	abs_path = os.path.join(args.directory, args.name)
	
	## If torrent is a single file
	if os.path.isfile(abs_path):
	
		## Create new directory
		new_dir = create_dir_owner(args)

		## Copy the file to the new directory
		abs_path = copy_file(new_dir, args)

	## If there are RAR files extract them into the top directory
	rar_files = files_with_ext(abs_path, "rar")
	for rar_file in rar_files:
		process = subprocess.Popen(["unrar", "x", rar_file], stdout=PIPE, stderr=PIPE)

	## Import all non-compressed video files
	video_files = [files_with_ext(abs_path, ext) for ext in allowed_ext]
	video_files = [i for sl in video_files for i in sl]
	for video in video_files:
		add_file_to_syno(video, synoclient_path)
		
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