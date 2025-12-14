#!/usr/bin/env python3
import io
import os
import re
from setuptools import setup, find_packages


def get_version():
    with open('ua_extract/__init__.py', 'r') as f:
        line = f.readline()
        match = re.match(r'__version__ = \'([\d\.]+)\'', line)

        if not match:
            raise ImportError("Can't read the version of device_detector")


def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

setup(
    name='ua_extract',
    version=get_version(),
    description="Python3 port of matomo's Device Detector",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Pranav Agrawal',
    author_email='pranavagrawal321@gmail.com',
    url='https://github.com/pranavagrawal321/ua_extract',
    packages=find_packages(exclude=["tests"]),
    package_dir={'': '.'},
    license='MIT',
    zip_safe=True,
    include_package_data=True,
    license_files=['LICENSE'],
    package_data={
        '': ['*.yml'],
    },
    python_requires='>=3.8',
    install_requires=parse_requirements('requirements.txt'),
    entry_points={
        "console_scripts": [
            "ua_extract=ua_extract.__main__:main",
        ],
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        "Source": "https://github.com/pranavagrawal321/ua_extract",
        "Issues": "https://github.com/pranavagrawal321/ua_extract/issues",
        "Documentation": "https://github.com/pranavagrawal321/ua_extract#readme",
    },
)
