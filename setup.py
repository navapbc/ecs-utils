"""setup.py."""
import os

from setuptools import find_packages, setup

INSTALL_DEPS = ['boto3>=1.8.5',
                'botocore>=1.11.5']

def read(fname):
    """Read a file from the filesystem."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="ecs-utils",
    version=read("VERSION"),
    author="Nava",
    author_email="devops@navapbc.com",
    description="Deployment scripts for ECS",
    license="MIT License",
    keywords="",
    install_requires=INSTALL_DEPS,
    packages=find_packages(),
    long_description=read("README.md"),
    python_requires='>=3.6.*',
    entry_points={
        "console_scripts": [
            "kms-create = scripts.kms_create:main",
            "kms-crypt = scripts.kms_crypt:main",
            "param = scripts.param:main",
            "service-check = scripts.service_check:main",
            "get-current-image = scripts.get_current_image:main",
            "rolling-replace = scripts.rolling_replace:main"
        ],
    },
)
