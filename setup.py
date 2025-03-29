import os
from setuptools import setup, find_packages

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="insurgent",
    version="0.1.0",
    author="InsurgeNT Team",
    author_email="bumbelbee437167@gmail.com",
    description="A modern dev shell and build system for C/C++ projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bumbelbee777/insurgent",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Shells",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "insurgent=insurgent:main",
        ],
    },
    install_requires=[
        "PyYAML",
    ],
) 