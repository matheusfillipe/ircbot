import re
import subprocess

import setuptools

VERSION = "2.0.12-dev"
BRANCH = "v2"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def requirements():
    """Build the requirements list for this project"""
    requirements_list = []

    with open("requirements.txt") as requirements:
        for install in requirements:
            requirements_list.append(install.strip())
    return requirements_list


def exec(cmd):
    """Execute a command and return the output"""
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode().strip()


def git_version_tag():
    """Get the current git version tag"""
    branch = exec("git rev-parse --abbrev-ref HEAD")
    version = re.match(r"^v[0-9]+(\.[0-9]+)*.*$", exec("git describe --tags --abbrev=0"))
    if branch == BRANCH and version:
        return version[0][1:]
    else:
        return VERSION


requirements = requirements()

# VERSION = git_version_tag()
print(f"BUILDING Version: {VERSION}")

setuptools.setup(
    name="re-ircbot",
    version=VERSION,
    author="Matheus Fillipe",
    author_email="mattf@tilde.club",
    description="A simple async irc bot framework with regex command definitions and data permanency",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matheusfillipe/ircbot",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
    ],
    python_requires=">=3.10",
)
