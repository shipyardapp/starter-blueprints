from setuptools import find_packages, setup

config = {
    "description": "Single function scripts to move and manage your data across multiple vendors.",
    "author": "Shipyard Team",
    "url": "https://github.com/shipyardapp/starter-blueprints",
    "author_email": "tech@shipyardapp.com",
    "packages": find_packages(),
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
