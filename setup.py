from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description: str = f.read()

setup(
    name='md_py_common',
    version='0.0.8',
    description="Mr. Hoorn's Python Common Library.'",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LordMartron94/py-common",
    author="Mr. Hoorn",
    author_email="md.career@protonmail.com",
    license="GNU General Public License v3.0",
    package_dir={"": "md_py_common"},
    packages=find_packages(where="md_py_common"),
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
