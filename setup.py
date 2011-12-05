'''
mynt
====

*Another static site generator?*

With the ever growing population of static site generators, more often
than not I found that they either had very simplistic support for blogs
or used template engines that for one reason or another irked me.

After not finding a solution I was happy with, just as any other
programmer would do, I decided to roll my own and wrote mynt with the
hope that others would find it useful as well.

Install
-------

| From PyPI:
| ``pip install mynt``

| Latest trunk:
| ``pip install git+https://github.com/Anomareh/mynt.git``

Getting Started
---------------

After installing mynt head on over and give the `docs`_ a read.

Dependencies
------------

-  `Jinja2`_
-  `misaka`_
-  `Pygments`_
-  `PyYAML`_

Support
-------

If you run into any issues or have any questions, either open an
`issue`_ or hop in #mynt on irc.freenode.net.

.. _docs: http://mynt.mirroredwhite.com/
.. _Jinja2: http://jinja.pocoo.org/
.. _misaka: http://misaka.61924.nl/
.. _Pygments: http://pygments.org/
.. _PyYAML: http://pyyaml.org/
.. _issue: https://github.com/Anomareh/mynt/issues
'''
from setuptools import find_packages, setup


setup(
    name = 'mynt',
    version = '0.1.1',
    author = 'Andrew Fricke',
    author_email = 'andrew@mirroredwhite.com',
    url = 'http://mynt.mirroredwhite.com/',
    description = 'A static blog generator.',
    long_description = __doc__,
    license = 'BSD',
    packages = find_packages(),
    entry_points = {
        'mynt.parsers.markdown': [
            'misaka = mynt.parsers.markdown.misaka:Parser'
        ],
        'mynt.renderers': [
            'jinja = mynt.renderers.jinja:Renderer'
        ],
        'console_scripts': 'mynt = mynt:main'
    },
    install_requires = [
        'Jinja2',
        'misaka',
        'Pygments',
        'PyYAML'
    ],
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
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing',
        'Topic :: Utilities'
    ]
)
