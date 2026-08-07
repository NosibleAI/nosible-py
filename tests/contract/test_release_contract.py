"""Release metadata and publishing-gate contracts."""

import os
from pathlib import Path

import pytest

from scripts.check_release import validate_release_ref

TEST_MODULE = os.path.basename(p=__file__)


pytestmark = pytest.mark.contract


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_release_tag_must_match_package_version() -> None:
    """
    Verify a matching version tag passes the release gate.

    :return: None.
    """
    validate_release_ref(
        version="0.4.0",
        ref_type="tag",
        ref_name="v0.4.0"
    )


def test_release_tag_rejects_mismatched_package_version() -> None:
    """
    Verify a mismatched version tag fails the release gate.

    :return: None.
    """
    with pytest.raises(
        expected_exception=ValueError,
        match="must exactly match"
    ):
        validate_release_ref(
            version="0.4.0",
            ref_type="tag",
            ref_name="v0.4.1"
        )


def test_branch_builds_do_not_require_release_tags() -> None:
    """
    Verify normal branch builds remain eligible for artifact validation.

    :return: None.
    """
    validate_release_ref(
        version="0.4.0",
        ref_type="branch",
        ref_name="main"
    )


def test_license_metadata_pins_a_verified_setuptools_minimum() -> None:
    """
    Verify license metadata declares the independently verified backend floor.

    :return: None.
    """
    project_metadata = (PROJECT_ROOT / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    setup_metadata = (PROJECT_ROOT / "setup.py").read_text(
        encoding="utf-8"
    )

    assert 'dynamic = ["license"]' in project_metadata
    assert 'requires = ["setuptools>=75.1.0", "wheel"]' in project_metadata
    assert 'license="MIT"' in setup_metadata
    assert 'license_files=["LICENSE"]' in setup_metadata


def test_publish_workflow_validates_tag_before_building() -> None:
    """
    Verify the publish workflow gates artifacts on exact release metadata.

    :return: None.
    """
    workflow = (
        PROJECT_ROOT / ".github" / "workflows" / "run_tests_and_publish.yml"
    ).read_text(encoding="utf-8")

    validation = workflow.index("Validate release metadata and tag")
    minimum_backend = workflow.index("Verify minimum supported build backend")
    build = workflow.index("Build distributions")
    assert validation < minimum_backend < build
    assert "python scripts/check_release.py" in workflow
    assert '"setuptools==75.1.0"' in workflow
    assert "python -m build --no-isolation" in workflow
    assert "twine check dist/*" in workflow


def test_ci_exercises_every_advertised_python_version() -> None:
    """
    Verify CI includes every Python version advertised by package metadata.

    :return: None.
    """
    workflow = (
        PROJECT_ROOT / ".github" / "workflows" / "run_tests_and_publish.yml"
    ).read_text(encoding="utf-8")

    assert (
        'python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]'
        in workflow
    )


def test_ci_runs_controlled_live_contract_checks() -> None:
    """
    Verify scheduled and manual CI exercise deployed Search and World contracts.

    :return: None.
    """
    workflow = (
        PROJECT_ROOT / ".github" / "workflows" / "run_tests_and_publish.yml"
    ).read_text(encoding="utf-8")

    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "Require live-test credentials" in workflow
    assert "uv venv" in workflow
    assert "pytest --run-integration -m integration --maxfail=1" in workflow


def test_world_docs_describe_public_first_authentication_fallback() -> None:
    """
    Verify World documentation agrees with public-first bearer fallback.

    :return: None.
    """
    world_docs = (PROJECT_ROOT / "docs" / "world.rst").read_text(
        encoding="utf-8"
    )

    assert "public-first" in world_docs
    assert "SDK-managed bearer" in world_docs
    assert "They never send" not in world_docs
