import os, sys, fnmatch, argparse, subprocess
from datetime import datetime

## Add modules from the submodule (vs-utils)
cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(cur_dir, "VS-Utils"))
from files import create_path_directories, file_copy, file_copy_args
from files import files_find_ext, files_unrar, files_fix_single
from prints import errmsg, debugmsg, infomsg, init_logging
from scope import scope_get, scope_map_path
from mediainfo import ffprobe_file
from parse import parse_cfg
from client import client

def parse_arguments():
    """ Parse the shell arguments

    Returns:
        Namespace -- Namespace containing all arguments
    """

    args = argparse.Namespace()
    parser = argparse.ArgumentParser(description='Post Processing of torrents via transmission')
    parser.add_argument('-n','--name',      help='Name of the torrent',      required=True)
    parser.add_argument('-d','--directory', help='Directory of the torrent', required=True)
    parser.add_argument('-u','--userid',    help='ID of the user (PUID)',    default=0, type=int, nargs='?')
    parser.add_argument('-g','--groupid',   help='ID of the group (PGID)',   default=0, type=int, nargs='?')
    args = parser.parse_args()
    args.script_dir = cur_dir
    args.scope = scope_get()

    ## Check whether the passed name and directory are valid
    if not os.path.isdir(args.directory):
        errmsg("Passed torrent directory does not exist", "Parsing", (args.directory,)); exit()
    full_path = os.path.join(args.directory, args.name)
    if (not os.path.isdir(full_path)) and (not os.path.isfile(full_path)):
        errmsg("Passed torrent does not exist", "Parsing", (full_path,)); exit()
    return args

def write_changelog_file(source, source_host, root):
    """ Write the changelog file to pass the new releases for the notification service.

    Arguments:
        source {string}      -- Path to the source within docker container.
        source_host {string} -- Path to the source on host system.
        root {string}        -- Path to the top mount containing the file.
    """

    ## Create changelog file path
    changelog_file = os.path.join(root, "changelog.txt")

    ## Write the convert file
    date = datetime.strftime(datetime.now(), "%Y-%m-%d")
    changelog_content = "{date},{source}\n".format(date=date, source=source_host)
    if os.path.isfile(changelog_file):
        with open(changelog_file, 'r') as f: lines = f.readlines()
        dupl = [l for l in lines if l.split(",")[0] == date and l.split(",")[1] == source_host]
        if (dupl):
            debugmsg("Item already exist in changelog file, skip it", "Postprocessing", (changelog_file,))
            return
        debugmsg("Add item to changelog file", "Postprocessing", (changelog_file,))
    else:
        debugmsg("Create changelog file and add item", "Postprocessing", (changelog_file,))
    with open(changelog_file, 'a') as f: f.write(changelog_content)

def write_convert_file(cfg, source, source_host, root_host, output_host, watch_host):
    """ Write the convert file to pass necessary filesystem information to handbrake.

    Arguments:
        cfg {Namespace}      -- Namespace containing all configurations.
        source {string}      -- Path to the source within docker container.
        source_host {string} -- Path to the source file on the host system.
        root_host {string}   -- Path to the top mount containing the file.
        output_host {string} -- Path to the output file of handbrake.
        watch_host {string}  -- Path to the watch file of handbrake.
    """

    ## Create convert file path
    convert_file = "%s.txt" % (".".join(os.path.basename(source).split(".")[:-1]))
    convert_file = os.path.join(cfg.handbrake, "convert", convert_file)

    ## Write the convert file
    convert_content = "root_host:{}\nsource_host:{}\noutput_host:{}\n" \
                      "watch_host:{}".format(root_host, source_host, output_host, watch_host)
    with open(convert_file, 'w+') as f: f.write(convert_content)
    debugmsg("Created convert file", "Postprocessing", (convert_file,))

def copy_file_to_handbrake(args, cfg, source, source_host, root_host):
    """ Copy file to the handbrake watch directory and change owner.

    Arguments:
        args {Namespace}     -- Namespace containing all shell arguments.
        cfg {Namespace}      -- Namespace containing all configurations.
        source {string}      -- Path to the source within docker container.
        source_host {string} -- Path to the source file on the host system.
        root_host {string}   -- Path to the top mount containing the file.
    """

    ## Get all media info about the file
    video_info = ffprobe_file(source)
    codec = video_info["video_codec"]
    resolution = video_info["resolutionY"]
    debugmsg("Analyse the video file for codec and resolution", "Mediainfo", (resolution, codec))

    ## Check whether it is one codec of the config is present
    if codec not in cfg.codecs:
        infomsg("Codec is not watched in file", "Postprocessing", (source, codec))
        return

    ## Only copy files which match no exclude string
    if any(exclude in source for exclude in cfg.exclude):
        infomsg("Source file excluded by config", "Postprocessing", (source,))
        return

    ## Switch the watch directory depending on the 4K mode and the resolution
    watch_host = os.path.join(cfg.handbrake, "watch")
    if (cfg.hb_4k == 1 and int(resolution) > 2000):
        infomsg("4K mode enabled - file is copied to separate watch directory", "Postprocessing", (watch_host,))
        watch_host = os.path.join(cfg.handbrake, "watch2")
    if not os.path.isdir(watch_host):
        create_path_directories(watch_host)
        os.chown(watch_host, cfg.host_admin[0], cfg.host_admin[1])

    ## Copy the video file to the handbrake watch directory
    infomsg("Copying file to handbrake watch directory", "Postprocessing", (watch_host,))
    watch_file = file_copy(source, watch_host, args)
    if not watch_file:
        errmsg("Could not copy file to handbrake watch directory", "Postprocessing", (watch_host,))
        return
    infomsg("Finished copying file", "Postprocessing", (watch_file,))

    output_file = os.path.join(cfg.handbrake, "output", os.path.basename(watch_file))
    output_host = scope_map_path(cfg, args, output_file)[0]
    if output_host == -1:
        errmsg("Could not get the host path of file", "Postprocessing", (output_file))
        return

    ## Write the convert file with all necessary information
    write_convert_file(cfg, source, source_host, root_host, output_host, watch_host)

def post_processing(args, cfg):
    """ Post processing.

    Arguments:
        args {Namespace}  -- Namespace containing all shell arguments.
        cfg {Namespace}   -- Namespace containing all configurations.
    """

    ## Initialize the logging
    init_logging(args, cfg)
    debugmsg("-" * 35, "Postprocessing")

    ## If torrent is a single file create a directory and copy that file
    abs_path = files_fix_single(args)

    ## If there are RAR files extract them into the top directory
    files_unrar(abs_path, cfg.extensions)

    ## Import all non-compressed video files
    source_files = files_find_ext(abs_path, cfg.extensions)
    for source in source_files:
        (source_host, root_host, root) = scope_map_path(cfg, args, source)
        infomsg("Add source file to SynoIndex database", "Postprocessing", (source_host.split(os.sep)[-1],))
        client(args.scope, cfg.port, source_host)

    ## Write changelog file for notification service
    write_changelog_file(source, source_host, root)

    ## Copy video file to handbrake if it's configured
    if (cfg.handbrake):
        for source in source_files:
            (source_host, root_host, _) = scope_map_path(cfg, args, source)
            copy_file_to_handbrake(args, cfg, source, source_host, root_host)

def main():
    ## Parse the shell arguments
    args = parse_arguments()

    ## Parse the config
    config_file = os.path.join(cur_dir, "config.txt")
    cfg = parse_cfg(config_file, "vs-transmission", args.scope)

    ## Check for userid and groupid in docker scope
    if (args.scope == "docker" and (args.userid == 0 or args.groupid == 0)):
        errmsg("Docker scope requires userid and groupid", "Post-Processing")
    elif(args.scope == "host"):
        args.userid, args.groupid = cfg.host_admin

    ## Post Processing
    post_processing(args, cfg)

if __name__ == "__main__":
    main()
