from setuptools import find_packages, setup

# Read the contents of your README file for the long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    # Package metadata
    name="nosible",
    version="0.1.0",
    author="Stuart Reid, Matthew Dicks, Richard Taylor, Gareth Warburton",
    author_email="stuart@nosible.com, matthew@nosible.com, richard@nosible.com, gareth@nosible.com",
    description="Python client for the NOSIBLE Search API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NosibleAI/nosible",
    project_urls={
        "Homepage": "https://github.com/NosibleAI/nosible",
        "Issues": "https://github.com/NosibleAI/nosible/issues",
    },
    license="MIT",
    classifiers=[
        # Development
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        # Supported Python versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
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
    # Dependencies
    install_requires=[
        "requests",
        "polars",
        "duckdb",
        "openai",
        "tantivy",
        "pyrate-limiter",
        "tenacity",
        "cryptography",
        "pandas",
        "pyarrow",
    ],
    # Entry points for CLI scripts (if any)
    entry_points={
        # "console_scripts": [
        #     "nosible-cli=nosible.cli:main",
        # ],
    },
)
