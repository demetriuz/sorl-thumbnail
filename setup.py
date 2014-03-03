# -*- encoding: utf8 -*-
from setuptools import setup, find_packages
from setuptools.command.test import test


setup(
    name='pythonthumbnail',
    version='0.0',
    description='Thumbnails for Python',
    long_description=open('README.rst').read(),
    author='Dmitry Lazarko',
    author_email='alt0064@gmail.com',
    license='BSD',
    url='https://github.com/demetriuz/python-thumbnail',
    packages=find_packages(exclude=['tests', 'tests.*']),
    platforms='any',
    zip_safe=False
)