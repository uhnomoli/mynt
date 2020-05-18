# -*- coding: utf-8 -*-

from codecs import open
from datetime import datetime
from os import makedirs, path as op, remove, walk
import re
import shutil
from sys import exc_info
import traceback

from watchdog.events import FileSystemEventHandler

from mynt.exceptions import FileSystemException
from mynt.utils import abspath, get_logger, normpath, Timer


logger = get_logger('mynt')


class Directory:
    def __init__(self, path):
        self.path = abspath(path)

        if self.is_root:
            raise FileSystemException('Directory cannot be root')


    def _ignored(self, path, names):
        return [name for name in names if name.startswith(('.', '_'))]


    def cp(self, destination, ignore = True):
        if self.exists:
            destination = Directory(destination)
            ignore = self._ignored if ignore else None

            if destination.exists:
                destination.rm()

            logger.debug('..  cp: %s', self.path)

            shutil.copytree(self.path, destination.path, ignore=ignore)

    def empty(self):
        if self.exists:
            for root, directories, files in walk(self.path):
                for d in directories[:]:
                    if not d.startswith(('.', '_')):
                        Directory(abspath(root, d)).rm()

                    directories.remove(d)

                for f in files:
                    if not f.startswith(('.', '_')):
                        File(abspath(root, f)).rm()

    def mk(self):
        if not self.exists:
            logger.debug('..  mk: %s', self.path)

            makedirs(self.path)

    def rm(self):
        if self.exists:
            logger.debug('..  rm: %s', self.path)

            shutil.rmtree(self.path)


    @property
    def exists(self):
        return op.isdir(self.path)

    @property
    def is_root(self):
        return op.dirname(self.path) == self.path


    def __eq__(self, other):
        return self.path == other

    def __iter__(self):
        for root, directories, files in walk(self.path):
            for d in directories[:]:
                if d.startswith(('.', '_')):
                    directories.remove(d)

            for f in files:
                if f.startswith(('.', '_')):
                    continue

                yield File(normpath(root, f))

    def __ne__(self, other):
        return self.path != other

    def __str__(self):
        return self.path

class EventHandler(FileSystemEventHandler):
    def __init__(self, source, callback):
        self._source = source
        self._callback = callback


    def _regenerate(self, path):
        path = path.replace(self._source, '')

        if re.search(r'/[._](?!assets|containers|posts|templates)', path):
            logger.debug('>> Skipping: %s', path)
        else:
            logger.info('>> Change detected in: %s', path)

            try:
                Timer.start()

                self._callback()

                logger.info('Regenerated in %.3fs', Timer.stop())
            except:
                t, v, tb = exc_info()
                lc = traceback.extract_tb(tb)[-1:][0]

                logger.error('!! %s', v)
                logger.error('..  file: %s', lc[0])
                logger.error('..  line: %s', lc[1])
                logger.error('..  in: %s', lc[2])

                pass


    def on_any_event(self, event):
        if event.event_type != 'moved':
            self._regenerate(event.src_path)

    def on_moved(self, event):
        self._regenerate(event.dest_path)

class File:
    def __init__(self, path, content = None):
        self.path = abspath(path)
        self.root = Directory(op.dirname(self.path))
        self.name, self.extension = op.splitext(op.basename(self.path))
        self.content = content


    def cp(self, destination):
        if self.exists:
            destination = File(destination)

            if self.path != destination.path:
                if not destination.root.exists:
                    destination.root.mk()

                logger.debug('..  cp: %s', self.path)

                shutil.copyfile(self.path, destination.path)

    def mk(self):
        if not self.exists:
            if not self.root.exists:
                self.root.mk()

            logger.debug('..  mk: %s', self.path)

            with open(self.path, 'w', encoding='utf-8') as f:
                if self.content is None:
                    self.content = ''

                f.write(self.content)

    def rm(self):
        if self.exists:
            logger.debug('..  rm: %s', self.path)

            remove(self.path)


    @property
    def content(self):
        if self._content is None and self.exists:
            with open(self.path, 'r', encoding='utf-8') as f:
                self._content = f.read()

        return self._content

    @content.setter
    def content(self, content):
        self._content = content

    @property
    def exists(self):
        return op.isfile(self.path)

    @property
    def mtime(self):
        if self.exists:
            return datetime.utcfromtimestamp(op.getmtime(self.path))


    def __str__(self):
        return self.path

