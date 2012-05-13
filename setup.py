# encoding: utf-8

from setuptools import find_packages, setup
from mynt import __version__


setup(
    name='mynt',
    version=str(__version__),
    author='Andrew Fricke',
    author_email='andrew@mirroredwhite.com',
    url='http://mynt.mirroredwhite.com/',
    description='A static blog generator.',
    long_description=open('README.rst').read(),
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'mynt.parsers.markdown': [
            'misaka=mynt.parsers.markdown.misaka:Parser'
        ],
        'mynt.renderers': [
            'jinja=mynt.renderers.jinja:Renderer'
        ],
        'console_scripts': 'mynt=mynt.main:main'
    },
    install_requires=[
        'Jinja2',
        'misaka>=1.0.2',
        'Pygments',
        'PyYAML',
        'watchdog'
    ],
    platforms='any',
    zip_safe=False,
    classifiers=[
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
