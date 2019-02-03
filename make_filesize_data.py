# -*- coding: utf-8 -*-
import argparse
import os
import stat
import struct
import sys
from collections import namedtuple


inodes_reg = set()


BLOCK_SIZE = 512
NAME_STRUCT = 'H'
ENTRY_HEADER_STRUCT = '?Q'
TERMINATOR_NAME = b''


DirEntryInfo = namedtuple('DirEntryInfo', ['is_dir', 'size', 'browsable'])


def write_name(name, output):
	output.write(struct.pack(NAME_STRUCT, len(name)))
	output.write(name)


def write_entry_header(info, output):
	output.write(struct.pack(ENTRY_HEADER_STRUCT, info.is_dir, info.size))


def write_dir_content(directory, output):
	try:
		files = list(os.listdir(directory))
	except (OSError, IOError):
		pass

	for f in files:
		path = os.path.join(directory, f)
		f = f.encode('utf-8', 'replace')
		if len(f) == 0:
			continue
		info = get_info(path)
		if info is None:
			continue
		if info.is_dir:
			write_dir(info, path, f, output)
		else:
			write_file(info, f, output)


def write_dir(info, directory, dirname, output):
	write_name(dirname, output)
	write_entry_header(info, output)
	write_dir_content(directory, output)
	write_name(TERMINATOR_NAME, output)


def write_file(info, filename, output):
	write_name(filename, output)
	write_entry_header(info, output)


def get_info(path):
	browsable = False
	try:
		is_dir = os.path.isdir(path) and not os.path.islink(path)
		if is_dir and not os.path.ismount(path): # browse only not mounted directories
			browsable = True
		st = os.stat(path)
	except (OSError, IOError):
		return

	if not is_dir and not stat.S_ISREG(st.st_mode): # skip special files
		return

	if st.st_ino in inodes_reg: # skip hard links
		return
	inodes_reg.add(st.st_ino)

	return DirEntryInfo(is_dir, st.st_blocks * BLOCK_SIZE, browsable)


def analyze(directory, output):
	write_dir_content(directory, output)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'directory',
		nargs=1,
		type=str,
		help="Directory to analyze"
	)
	parser.add_argument(
		'outfile',
		nargs=1,
		type=argparse.FileType('wb'),
		help="Output file"
	)
	args = parser.parse_args(sys.argv[1:])
	analyze(args.directory[0], args.outfile[0])


if __name__ == "__main__":
	main()
