# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements_3.7.txt').read().split('\n')

setup(
    name='ocrd_webapi',
    version='0.0.1',
    description='Implementation of the OCR-D Web API',
    long_description=open('readme.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/OCR-D/ocrd-webapi-implementation',
    license='Apache License 2.0',
    install_requires=install_requires,
    packages=['ocrd_webapi',
              'ocrd_webapi.routers'
              ],
    package_data={'': ['things/']},
)
