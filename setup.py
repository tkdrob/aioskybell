"""The setup script."""
from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

setup(
    name="aioskybell",
    version="master",
    author="Robert Hillis",
    author_email="tkdrob4390@yahoo.com",
    description="A Skybell HD Python library running on Python 3.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/tkdrob/aioskybell",
    package_data={"aioskybell": ["py.typed"]},
    packages=find_packages(include=["aioskybell", "aioskybell*"]),
    install_requires=["aiohttp>=3.6.1,<4.0", "aiofiles>=0.3.0"],
    keywords=["aioskybell", "skybell"],
    license="MIT license",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
)
