from setuptools import find_packages, setup

# Read the contents of your README file for the long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    # Package metadata
    name="nosible",
    author="Stuart Reid, Matthew Dicks, Richard Taylor, Gareth Warburton",
    author_email="stuart@nosible.com, matthew@nosible.com, richard@nosible.com, gareth@nosible.com",
    description="Python client for the NOSIBLE Search API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NosibleAI/nosible",
    classifiers=[
        # Development
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Financial and Insurance Industry",
        # Supported Python versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3 :: Only",
        # Topics
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        # OS Compatibility
        "Operating System :: OS Independent",
    ],
    # Package discovery
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    python_requires=">=3.9",
)
