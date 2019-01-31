# fuse-filesize

This software is used to create a list of files with their sizes and to mount the this list as real filesystem.

# Motivation

I wanted to graphically visualize the used space on server disk. Every tool I tried (sshfs, ftpfs ...) was too slow. That's why I wrote a tool that writes the file list on the server disk and the tool that mounts this list.

# Usage

First create file list (on remote server or local machine).

```
# python3 make_filesize_data.py <directory> <filename>

python3 make_filesize_data.py / ~/filesize_data
```

Then we move `filesize_data` file to another machine and mount this file.

```
mkdir mnt
python filesize_fuse.py --stats_file filesize_data mnt
```
