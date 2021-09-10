import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def requirements():
    """Build the requirements list for this project"""
    requirements_list = []

    with open('requirements.txt') as requirements:
        for install in requirements:
            requirements_list.append(install.strip())
    return requirements_list

requirements = requirements()

setuptools.setup(
    name="re-ircbot", # Replace with your own username
    version="1.3.98",
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
    python_requires=">=3.4",
)
