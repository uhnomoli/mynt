'''
mynt
----

*Another static site generator?*

With the ever growing population of static site generators, all filling a
certain need, I've yet to find one that allows the generation of anything but
the simplest of blogs.

That's where mynt comes in, being designed to give you all the features of a
CMS with none of the often rigid implementations of those features.


Install
=======

From PyPI::

    $ pip install mynt

Latest trunk::

    $ pip install git+https://github.com/Anomareh/mynt.git


Getting started
===============

After installing mynt head on over and give the `quickstart`_ page and `docs`_ a read.


Dependencies
============

+ `houdini.py`_
+ `Jinja2`_
+ `misaka`_
+ `Pygments`_
+ `PyYAML`_
+ `watchdog`_

Optional
~~~~~~~~

+ `Docutils`_ *(reST)*


Support
=======

If you run into any issues or have any questions, either open an `issue`_ or
hop in #mynt on irc.freenode.net.

.. _docs: http://mynt.mirroredwhite.com/
.. _Docutils: http://docutils.sourceforge.net/
.. _houdini.py: http://python-houdini.61924.nl/
.. _issue: https://github.com/Anomareh/mynt/issues
.. _Jinja2: http://jinja.pocoo.org/
.. _misaka: http://misaka.61924.nl/
.. _Pygments: http://pygments.org/
.. _PyYAML: http://pyyaml.org/
.. _quickstart: http://mynt.mirroredwhite.com/docs/quickstart/
.. _watchdog: http://packages.python.org/watchdog/
'''
from setuptools import find_packages, setup

from mynt import __version__


setup(
    name = 'mynt',
    version = str(__version__),
    author = 'Andrew Fricke',
    author_email = 'andrew@mirroredwhite.com',
    url = 'http://mynt.mirroredwhite.com/',
    description = 'A static site generator.',
    long_description = __doc__,
    license = 'BSD',
    packages = find_packages(),
    include_package_data = True,
    entry_points = {
        'mynt.parsers' : [
            'docutils = mynt.parsers.docutils:Parser [reST]',
            'misaka = mynt.parsers.misaka:Parser'
        ],
        'mynt.renderers': [
            'jinja = mynt.renderers.jinja:Renderer'
        ],
        'console_scripts': 'mynt = mynt.main:main'
    },
    install_requires = [
        'houdini.py',
        'Jinja2==2.7',
        'misaka>=1.0.2',
        'Pygments',
        'PyYAML',
        'watchdog'
    ],
    extras_require = {
        'reST': 'docutils>=0.10'
    },
    platforms = 'any',
    zip_safe = False,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing',
        'Topic :: Utilities'
    ]
)
