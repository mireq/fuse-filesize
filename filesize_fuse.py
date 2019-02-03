# -*- coding: utf-8 -*-
import errno
import os
import stat
import struct

import fuse
from fuse import Fuse


NAME_STRUCT = 'H'
ENTRY_HEADER_STRUCT = '?Q'
TERMINATOR_NAME = b''

NAME_HEADER_SIZE = struct.calcsize(NAME_STRUCT)
ENTRY_HEADER_SIZE = struct.calcsize(ENTRY_HEADER_STRUCT)


if not hasattr(fuse, '__version__'):
	raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")


fuse.fuse_python_api = (0, 2)


def read_name(fp):
	name_header_bytes = fp.read(NAME_HEADER_SIZE)
	if len(name_header_bytes) != NAME_HEADER_SIZE:
		return None
	(size,) = struct.unpack(NAME_STRUCT, name_header_bytes)
	name = fp.read(size)
	if len(name) != size:
		return None
	return name


def read_entry_header(fp):
	entry_header_bytes = fp.read(ENTRY_HEADER_SIZE)
	if len(entry_header_bytes) != ENTRY_HEADER_SIZE:
		return None
	(is_dir, size,) = struct.unpack(ENTRY_HEADER_STRUCT, entry_header_bytes)
	return (is_dir, size)


class Stat(fuse.Stat):
	def __init__(self):
		self.st_mode = 0
		self.st_ino = 0
		self.st_dev = 0
		self.st_nlink = 0
		self.st_uid = 0
		self.st_gid = 0
		self.st_size = 0
		self.st_atime = 0
		self.st_mtime = 0
		self.st_ctime = 0


class FilesizeFuse(Fuse):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.stats_file = ''
		self.dirs = {}

	def main(self, *args, **kwargs):
		self.read_stats()
		super().main(*args, **kwargs)

	def read_stats(self):
		try:
			fp = open(self.stats_file, 'rb')
		except IOError:
			raise RuntimeError("Stats file not initialized")
		self.read_stats_file(fp)
		fp.close()

	def read_stats_file(self, fp):
		dirname = '/'
		self.dirs = {'/': {}}
		while True:
			name = read_name(fp)
			if name is None:
				return
			if name == TERMINATOR_NAME:
				dirname = os.path.dirname(dirname)
				continue
			is_dir, size = read_entry_header(fp)
			name = name.decode('utf-8', 'replace')
			self.dirs[dirname][name] = size
			if is_dir:
				dirname = os.path.join(dirname, name)
				self.dirs[dirname] = {}

	def getattr(self, path):
		direntry = self.dirs.get(path)
		if direntry is None: # file
			parent_dir = os.path.dirname(path)
			basename = os.path.basename(path)
			direntry = self.dirs.get(parent_dir)
			if direntry is None:
				return -errno.ENOENT
			fileentry = direntry.get(basename)
			if fileentry is None:
				return -errno.ENOENT
			st = Stat()
			st.st_mode = stat.S_IFREG | 0o444
			st.st_nlink = 1
			st.st_size = direntry[basename]
			return st
		else: #  directory
			st = Stat()
			st.st_mode = stat.S_IFDIR | 0o755
			st.st_nlink = len(self.dirs[path]) + 2
			return st

	def readdir(self, path, offset):
		direntry = self.dirs.get(path)
		if direntry is None:
			return -errno.ENOENT

		yield fuse.Direntry('.')
		yield fuse.Direntry('..')
		for f in direntry.keys():
			yield fuse.Direntry(f)


def main():
	usage = "Filesystem for file size\n\n" + Fuse.fusage

	server = FilesizeFuse(version="%prog " + fuse.__version__, usage=usage, dash_s_do='setsingle')
	server.parser.add_option(
		'--stats_file',
		nargs=1,
		help="Stats file"
	)
	server.parse(values=server)
	if not server.stats_file:
		return
	server.main()


if __name__ == "__main__":
	main()
