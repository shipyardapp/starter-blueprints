from pathlib import Path
from pip.req import parse_requirements
from setuptools import find_packages, setup


install_requires = []
for path in Path('./').rglob('requirements.txt'):
    _reqs = parse_requirements(str(path.absolute()), session='hack')
    reqs = [str(r.req) for r in _reqs]
    install_requires.extend(reqs)


config = {
    "description": "Single function scripts to move and manage your data across multiple vendors.",
    "author": "Shipyard Team",
    "url": "https://github.com/shipyardapp/starter-blueprints",
    "author_email": "tech@shipyardapp.com",
    "packages": find_packages(),
    "install_requires": install_requires,
    "name": "shipyard_starter_blueprints",
    "license": "Apache-2.0",
    "classifiers": [
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Other Audience",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
}

setup(**config)
