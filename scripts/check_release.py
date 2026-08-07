"""Validate NOSIBLE package versions and release-tag metadata."""

import os
import re
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_VERSION_PATTERN = re.compile(
    pattern=r'(?m)^version = "([^"]+)"$'
)
PACKAGE_VERSION_PATTERN = re.compile(
    pattern=r'(?m)^__version__ = os\.fspath\(path="([^"]+)"\)$'
)
DOCS_VERSION_PATTERN = re.compile(
    pattern=r'(?m)^release = "([^"]+)"$'
)


def main() -> int:
    """
    Validate checked-in versions and the active GitHub release tag.

    :return: Zero when all release metadata is consistent.
    """
    version = read_version(
        path=PROJECT_ROOT / "pyproject.toml",
        pattern=PYPROJECT_VERSION_PATTERN,
        label="project"
    )
    package_version = read_version(
        path=PROJECT_ROOT / "src" / "nosible" / "__init__.py",
        pattern=PACKAGE_VERSION_PATTERN,
        label="package"
    )
    docs_version = read_version(
        path=PROJECT_ROOT / "docs" / "conf.py",
        pattern=DOCS_VERSION_PATTERN,
        label="documentation"
    )
    if len({version, package_version, docs_version}) != 1:
        raise ValueError(
            "Release versions disagree: "
            f"project={version}, package={package_version}, docs={docs_version}"
        )
    validate_release_ref(
        version=version,
        ref_type=os.environ.get("GITHUB_REF_TYPE"),
        ref_name=os.environ.get("GITHUB_REF_NAME")
    )
    print(f"Release metadata is consistent at {version}.")
    return 0


def read_version(
    path: Path,
    pattern: re.Pattern[str],
    label: str
) -> str:
    """
    Read one version value from a repository file.

    :param path: File containing the version declaration.
    :param pattern: Compiled pattern capturing the version.
    :param label: Human-readable source label.
    :return: Captured version.
    """
    match = pattern.search(
        string=path.read_text(encoding="utf-8")
    )
    if match is None:
        raise ValueError(f"Could not find the {label} version in {path}.")
    return match.group(1)


def validate_release_ref(
    version: str,
    ref_type: Optional[str],
    ref_name: Optional[str]
) -> None:
    """
    Require GitHub release tags to equal the package version exactly.

    :param version: Validated package version.
    :param ref_type: GitHub reference type.
    :param ref_name: GitHub branch or tag name.
    :return: None.
    """
    if ref_type != "tag":
        return
    expected_tag = f"v{version}"
    if ref_name != expected_tag:
        raise ValueError(
            f"Release tag {ref_name!r} must exactly match {expected_tag!r}."
        )


if __name__ == "__main__":
    raise SystemExit(main())
