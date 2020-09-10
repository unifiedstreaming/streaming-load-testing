# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

setup(
    name='streamin-load-testing',
    version='0.1.0',
    description='Load testing for video streaming setups',
    long_description=readme,
    author='R. Ramos-Chavez',
    packages=find_packages(exclude=('tests', 'docs'))
)
