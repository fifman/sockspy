#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0'
]

setup_requirements = [
    'pytest-runner'
]

test_requirements = [
    'pytest',
    'requests'
]

setup(
    name='sockspy',
    version='0.2.4',
    description="A python socks5 proxy implementation.",
    long_description=readme + '\n\n' + history,
    author="Fifman Feng",
    author_email='fifmanyc@gmail.com',
    url='https://github.com/fifman/sockspy',
    packages=find_packages(include=['sockspy', 'sockspy.*']),
    entry_points={
        'console_scripts': [
            'sockspy=sockspy.cli:main'
        ]
    },
    # include_package_data=True,
    package_data={
        '': ['*.yaml']
    },
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='sockspy',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        # "Programming Language :: Python :: 2",
        # 'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
