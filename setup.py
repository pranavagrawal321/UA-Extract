#!/usr/bin/env python3
import io
import os
import re
from setuptools import setup, find_packages


def get_version():
    with open('ua_extract/__init__.py', 'r') as f:
        for line in f:
            match = re.match(r"__version__\s*=\s*['\"]([\d\.]+)['\"]", line)
            if match:
                return match.group(1)
    raise ImportError("Can't find version string in ua_extract/__init__.py")


here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

setup(
    name='device_detector',
    version=get_version(),
    description="Python3 port of matomo's Device Detector",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Dave Burkholder',
    author_email='pranavagrawal321@gmail.com',
    packages=find_packages(exclude=["tests"]),
    package_dir={'': '.'},
    include_package_data=True,
    package_data={'': ['*.yml']},
    license='MIT',
    zip_safe=True,
    url='https://github.com/pranavagrawal321/ua_extract',
    install_requires=[
        'pyyaml',
        'regex',
    ],
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
