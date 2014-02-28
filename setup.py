# -*- encoding: utf8 -*-
from setuptools import setup, find_packages
from setuptools.command.test import test


__author__ = "Mikko Hellsing"
__license__ = "BSD"
__version__ = '0.0'
__maintainer__ = "Mario César Señoranis Ayala"
__email__ = "mariocesar@creat1va.com"


setup(
    name='pythonthumbnail',
    version=__version__,
    description='Thumbnails for Python',
    long_description=open('README.rst').read(),
    author=__author__,
    author_email='mikko@aino.se',
    maintainer=__maintainer__,
    maintainer_email=__email__,
    license=__license__,
    url='https://github.com/demetriuz/python-thumbnail',
    packages=find_packages(exclude=['tests', 'tests.*']),
    platforms='any',
    zip_safe=False
)