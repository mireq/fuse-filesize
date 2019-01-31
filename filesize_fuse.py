# -*- coding: utf-8 -*-
import errno
import os
import stat
import struct

import fuse
from fuse import Fuse


DIR_ITEM = 0
DIR_ENTRY = 1
FILE_ENTRY = 2


if not hasattr(fuse, '__version__'):
	raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")


fuse.fuse_python_api = (0, 2)


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
		self.dirs = {'/': {}}

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
		header_size = struct.calcsize('?QH')
		dirname = '/'
		while True:
			header = fp.read(header_size)
			if len(header) != header_size:
				break
			mode, filesize, stringsize = struct.unpack('bQH', header)
			filename = fp.read(stringsize)
			if len(filename) != stringsize:
				break
			filename = filename.decode('utf-8', 'replace')
			if mode == DIR_ITEM:
				dirname = filename
				self.dirs[dirname] = {}
			else:
				self.dirs[dirname][filename] = filesize

	def getattr(self, path):
		st = Stat()
		if path in self.dirs:
			st.st_mode = stat.S_IFDIR | 0o755
			st.st_nlink = len(self.dirs[path])
		else:
			parent_dir = os.path.dirname(path)
			basename = os.path.basename(path)
			if parent_dir in self.dirs:
				direntry = self.dirs[parent_dir]
				if basename in direntry:
					st.st_mode = stat.S_IFREG | 0o444
					st.st_nlink = 1
					st.st_size = direntry[basename]
				else:
					return -errno.ENOENT
			else:
				return -errno.ENOENT
		return st

	def readdir(self, path, offset):
		if path not in self.dirs:
			return -errno.ENOENT

		direntry = self.dirs[path]
		files = list(direntry.keys())
		files.sort()
		files = ['.', '..'] + files
		for f in files:
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
