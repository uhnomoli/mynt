# -*- coding: utf-8 -*-

from os import path as op

from setuptools import find_packages, setup

from mynt import __version__


root = op.abspath(op.dirname(__file__))
with open(op.join(root, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='mynt',
    version=__version__,
    author='Andrew Fricke',
    author_email='andrew@uhnomoli.com',
    url='https://mynt.uhnomoli.com/',
    project_urls={
        'Documentation': 'https://mynt.uhnomoli.com/docs/quickstart/',
        'Source': 'https://github.com/Anomareh/mynt'},
    description='A static site generator.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='BSD',
    platforms='any',
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'mynt.parsers' : [
            'docutils=mynt.parsers.docutils:Parser [reST]',
            'hoep=mynt.parsers.hoep:Parser'],
        'mynt.renderers': [
            'jinja=mynt.renderers.jinja:Renderer'],
        'console_scripts': 'mynt=mynt.main:main'},
    python_requires='~=3.5',
    install_requires=[
        'hoep>=1.0.2',
        'Jinja2>=2.7.2',
        'Pygments',
        'PyYAML',
        'watchdog'],
    extras_require={
        'reST': 'docutils>=0.10'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing',
        'Topic :: Utilities'])

