# -*- coding: utf-8 -*-
import argparse
import os
import stat
import struct
import sys


inodes_reg = set()


def make_local_name(base_dir, directory, filename):
	filename = os.path.join(directory, filename)
	filename = filename[len(base_dir):]
	if filename[0] != '/':
		filename = '/' + filename
	return filename


def write_dir_item(local_name, st, output):
	local_name = local_name.encode('utf-8', 'replace')
	output.write(struct.pack('bQH', 0, st.st_size, len(local_name)))
	output.write(local_name)


def write_entry_item(local_name, is_file, st, output):
	local_name = local_name.encode('utf-8', 'replace')
	output.write(struct.pack('bQH', 2 if is_file else 1, st.st_size, len(local_name)))
	output.write(local_name)


def write_dir(base_dir, directory, output):
	try:
		files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) or os.path.islink(os.path.join(directory, f))]
		dirs = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f)) and not os.path.islink(os.path.join(directory, f))]
	except (OSError, IOError):
		return
	files.sort()
	dirs.sort()
	for f in files:
		path = os.path.join(directory, f)
		try:
			st = os.stat(path)
		except (OSError, IOError):
			continue
		if not stat.S_ISREG(st.st_mode):
			continue
		if st.st_ino in inodes_reg:
			continue
		inodes_reg.add(st.st_ino)
		write_entry_item(f, True, st, output)
	for f in dirs:
		path = os.path.join(directory, f)
		try:
			st = os.stat(path)
		except (OSError, IOError):
			continue
		write_entry_item(f, False, st, output)
	for f in dirs:
		path = os.path.join(directory, f)
		try:
			st = os.stat(path)
		except (OSError, IOError):
			continue
		local_name = make_local_name(base_dir, directory, f)
		write_dir_item(local_name, st, output)
		if not os.path.ismount(path):
			write_dir(base_dir, path, output)


def analyze(directory, output):
	write_dir(directory, directory, output)


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
