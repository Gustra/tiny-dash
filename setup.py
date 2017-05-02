# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='tiny-dash',
    version='0.1.0',
    description='Tiny dashboard application',
    long_description=readme,
    author='Gunnar Strand',
    author_email='Gurra.Strand@gmail.com',
    url='https://github.com/kennethreitz/samplemod',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
