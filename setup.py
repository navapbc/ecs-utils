"""setup.py."""
import os

from setuptools import find_packages, setup


def read(fname):
    """Read a file from the filesystem."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="ecs-scripts",
    version=read("VERSION"),
    author="Nava",
    author_email="devops@navahq.com",
    description="Deployment scripts for ECS",
    license="MIT License",
    keywords="",
    packages=find_packages(),
    long_description=read("README.md"),
    entry_points={
        "console_scripts": [
            "kms_create = scripts.kms_create:main",
            "kms_crypt = scripts.kms_crypt:main",
            "sns = scripts.sns:main",
            "param = scripts.param:main",
            "service_check = scripts.service_check:main",
            "rolling_replace = scripts.rolling_replace:main"
        ],
    },
)
