"""Compatibility setup entry point for the NOSIBLE package."""

import os

from setuptools import find_packages, setup


def main() -> None:
    """
    Run the setuptools compatibility entry point.

    :return: None.
    """
    readme_path = os.fspath(path="README.md")
    with open(
        file=readme_path,
        encoding="utf-8"
    ) as file_handle:
        long_description = file_handle.read()
    setup(
        name="nosible",
        author=(
            "Stuart Reid, Matthew Dicks, Richard Taylor, Gareth Warburton"
        ),
        author_email=(
            "stuart@nosible.com, matthew@nosible.com, "
            "richard@nosible.com, gareth@nosible.com"
        ),
        description="Python client for the NOSIBLE Search and World APIs",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/NosibleAI/nosible-py",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Intended Audience :: Information Technology",
            "Intended Audience :: Science/Research",
            "Intended Audience :: Financial and Insurance Industry",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Programming Language :: Python :: 3 :: Only",
            "Topic :: Software Development :: Libraries",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
            "Operating System :: OS Independent"
        ],
        package_dir={
            "": "src"
        },
        packages=find_packages(where="src"),
        include_package_data=True,
        license="MIT",
        license_files=["LICENSE"],
        python_requires=">=3.9"
    )


if __name__ == "__main__":
    main()
