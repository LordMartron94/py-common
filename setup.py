from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description: str = f.read()

setup(
    name='py_common',
    version='1.0.0',
    description="Mr. Hoorn's Python Common Library.'",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LordMartron94/py-common",
    author="Mr. Hoorn",
    author_email="md.career@protonmail.com",
    license="GNU General Public License v3.0",
    package_dir={'py_common': 'py_common'},
    packages=['py_common'] + ['py_common.' + p for p in find_packages(where='py_common')],
    package_data={
        "": ['*.json', '*.txt']
    },
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "colorama",
        "pydantic",
    ],
    python_requires=">=3.11",
)
