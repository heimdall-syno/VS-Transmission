import os, sys, fnmatch, argparse, subprocess
from datetime import datetime

## Add modules from the submodule (vs-utils)
cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(cur_dir, "VS-Utils"))
from files import files_find_ext, file_copy, file_copy_args
from files import directory_create_owner, unrar_files
from prints import errmsg, debugmsg, init_logging
from mediainfo import ffprobe_file
from parse import parse_cfg
from client import client

def scope_map_docker_path(mapping, filepath):
    """ Convert a path within docker container to hostsystem path.

    Arguments:
        mapping {list}      -- List of tuple representing the docker container mounts.
        filepath {string}   -- File path which should be mapped.

    Returns:
        string  -- Mapped file path.
    """

    ## Sanity check
    if not any(m[0] in filepath for m in mapping):
        return -1

    ## Map the docker path to the host path
    for m in mapping:
            file_tmp = filepath.replace(m[0], m[1])
            if file_tmp != filepath:
                (source_host, root_host, root) = (file_tmp, m[1], m[0])
    return (source_host, root_host, root)

def scope_map_path(cfg, args, filepath):
    """ Map docker path to host system path if necessary. If the scope
        is the host system the original path remains unchanged. The root
        directory is selected using the watch directories.

    Arguments:
        args {Namespace}    -- Namespace containing all shell arguments
        cfg {Namespace}     -- Namespace containing all configurations
        filepath {string}   -- File path which should be mapped.

    Returns:
        string  -- Mapped file path.
    """

    ## Map docker path to host system path
    if (args.scope == "docker"):
        return scope_map_docker_path(cfg.mapping, filepath)

    ## If script runs under host system then use the watch directories
    else:
        (source_host, root_host) = [(filepath, d) for d in cfg.watch_directories if d in filepath][0]
        return (source_host, root_host, root_host)

def scope_get():
    ''' Get the scope of the script (within docker container or host system) '''

    cgroup_path = os.path.join(os.sep, "proc", "1" , "cgroup")
    with open(cgroup_path, 'r') as f: groups = f.readlines()
    groups = list(set([g.split(":")[-1] for g in groups]))
    if (len(groups) == 1 and groups[0] == os.sep):
        return "host"
    return "docker"

def write_changelog_file(source, source_host, root):
    """ Write the changelog file to pass the new releases for the notification service.

    Arguments:
        source {string}      -- Path to the source within docker container.
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

def write_convert_file(cfg, source, source_host, root_host, output_host):
    """ Write the convert file to pass necessary filesystem information to handbrake.

    Arguments:
        source {string}      -- Path to the source within docker container.
        source_host {string} -- Path to the source file on the host system.
        root_host {string}      -- Path to the top mount containing the file.
        output_host {[type]} -- Path to the output file of handbrake.
    """

    ## Create convert file path
    convert_file = "%s.txt" % (".".join(os.path.basename(source).split(".")[:-1]))
    convert_file = os.path.join(cfg.handbrake, "convert", convert_file)

    ## Write the convert file
    convert_content = "root_host:%s\nsource_host:%s\noutput_host:%s" % (root_host, source_host, output_host)
    with open(convert_file, 'w+') as f: f.write(convert_content)
    debugmsg("Created convert file", "Postprocessing", (convert_file,))

def copy_file_to_handbrake(args, cfg, source, source_host, root_host):
    """ Copy file to the handbrake watch directory and change owner.

    Arguments:
        args {Namespace}      -- Namespace containing all shell arguments
        cfg {Namespace}      -- Namespace containing all configurations
        source {string}      -- Path to the source within docker container.
        source_host {string} -- Path to the source file on the host system.
        root_host {string}      -- Path to the top mount containing the file.
    """

    ## Get all media info about the file
    codec = ffprobe_file(source)["video_codec"]

    ## Check whether it is one codec of the config is present
    if codec not in cfg.codecs:
        debugmsg("Codec is not watched in file", "Postprocessing", (source, codec))
        return

    ## Only copy files which match no exclude string
    if any(exclude in source for exclude in cfg.exclude):
        debugmsg("Source file excluded by config", "Postprocessing", (source))
        return

    ## Copy the video file to the handbrake watch directory
    watch_dir = os.path.join(cfg.handbrake, "watch")
    debugmsg("Copying file to handbrake watch directory", "Postprocessing", (source,))
    watch_file = file_copy(source, watch_dir, args)
    if not watch_file:
        errmsg("Could not copy file to handbrake watch directory", "Postprocessing", (source,))
        return
    debugmsg("Finished copying file", "Postprocessing", (source,))

    output_file = os.path.join(cfg.handbrake, "output", os.path.basename(watch_file))
    output_host = scope_map_path(cfg,args, output_file)[0]
    if output_host == -1:
        errmsg("Could not get the host path of file", "Postprocessing", (output_file))
        return

    ## Write the convert file with all necessary information
    write_convert_file(cfg, source, source_host, root_host, output_host)

def fix_single_file(args):
    """ If a single video file was downloaded create a directory and copy the file """

    abs_path = os.path.join(args.directory, args.name)
    if os.path.isfile(abs_path):
        new_dir = directory_create_owner(args)
        abs_path = file_copy(abs_path, new_dir, args)
        debugmsg("Fixed single video file into directory", "Postprocessing", (new_dir,))
    return abs_path

def post_processing(args):
    ''' Post processing '''

    ## Parse the config
    config_file = os.path.join(cur_dir, "config.txt")
    cfg = parse_cfg(config_file, "vs-transmission", args.scope)

    ## Initialize the logging
    init_logging(args)

    ## If torrent is a single file create a directory and copy that file
    abs_path = fix_single_file(args)

    ## If there are RAR files extract them into the top directory
    unrar_files(abs_path)

    ## Import all non-compressed video files
    source_files = files_find_ext(abs_path, cfg.extensions)
    for source in source_files:
        (source_host, root_host, root) = scope_map_path(cfg, args, source)
        debugmsg("Add source file to SynoIndex database", "Postprocessing", (source_host.split(os.sep)[-1],))
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
    args = argparse.Namespace()
    parser = argparse.ArgumentParser(description='Post Processing of torrents via transmission')
    parser.add_argument('-n','--name', help='Name of the torrent', required=True)
    parser.add_argument('-d','--directory', help='Directory of the torrent', required=True)
    parser.add_argument('-u','--userid', help='ID of the user (PUID)', type=int, required=True)
    parser.add_argument('-g','--groupid', help='ID of the group (PGID)', type=int, required=True)
    args = parser.parse_args()
    args.script_dir = cur_dir
    args.scope = scope_get()

    ## Post Processing
    post_processing(args)

if __name__ == "__main__":
    main()
