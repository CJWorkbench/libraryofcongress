#!/usr/bin/env python

from setuptools import setup

setup(
    name='libraryofcongress',
    version='0.0.1',
    description='Search the Library of Congress for document records',
    author='Adam Hooper',
    author_email='adam@adamhooper.com',
    url='https://github.com/CJWorkbench/libraryofcongress',
    packages=[''],
    py_modules=['libraryofcongress'],
    install_requires=['pandas==0.24.2', 'aiohttp', "cjwmodule==*"]
)
