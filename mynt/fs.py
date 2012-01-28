# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from codecs import open
from datetime import datetime
from os import makedirs, path as op, walk
import shutil

from mynt.utils import abspath, get_logger, normpath


logger = get_logger('mynt')


class Directory(object):
    def __init__(self, path):
        self.path = abspath(path)
    
    
    def mk(self):
        if not self.exists:
            logger.debug('..  mk: {0}'.format(self.path))
            
            makedirs(self.path)
    
    def rm(self):
        if self.exists:
            logger.debug('..  rm: {0}'.format(self.path))
            
            shutil.rmtree(self.path)
    
    
    @property
    def exists(self):
        return op.exists(self.path) and op.isdir(self.path)
    
    
    def __eq__(self, other):
        return self.path == other
    
    def __iter__(self):
        for root, dirs, files in walk(self.path):
            for d in dirs[:]:
                if d.startswith(('.', '_')):
                    dirs.remove(d)
            
            for f in files:
                if f.startswith(('.', '_')):
                    continue
                
                yield File(normpath(root, f))
    
    def __ne__(self, other):
        return self.path != other
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.path

class File(object):
    def __init__(self, path, content = None):
        self.path = abspath(path)
        self.root = Directory(op.dirname(self.path))
        self.name, self.extension = op.splitext(op.basename(self.path))
        self.content = content
    
    
    def cp(self, dest):
        dest = File(dest)
        
        logger.debug('..  cp: {0}{1}\n..      src:  {2}\n..      dest: {3}'.format(self.name, self.extension, self.root, dest.root))
        
        if dest.exists:
            dest.rm()
        elif not dest.root.exists:
            dest.root.mk()
        
        shutil.copyfile(self.path, dest.path)
    
    def mk(self):
        if not self.exists:
            logger.debug('..  mk: {0}'.format(self.path))
            
            if not self.root.exists:
                self.root.mk()
            
            with open(self.path, 'w', encoding = 'utf-8') as f:
                if self.content is None:
                    self.content = ''
                
                f.write(self.content)
    
    
    @property
    def content(self):
        if self._content is None and self.exists:
            with open(self.path, 'r', encoding = 'utf-8') as f:
                self._content = f.read()
        
        return self._content
    
    @content.setter
    def content(self, content):
        self._content = content
    
    @property
    def exists(self):
        return op.exists(self.path) and op.isfile(self.path)
    
    @property
    def mtime(self):
        if self.exists:
            return datetime.utcfromtimestamp(op.getmtime(self.path))
    
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.path
