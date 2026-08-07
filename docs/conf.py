"""Sphinx configuration for the NOSIBLE Python SDK."""

import os
import sys
from typing import Any, Optional

sys.path.insert(
    0,
    os.path.abspath(path="../src")
)

project = "NOSIBLE Python SDK"
copyright = "2026, NOSIBLE"
author = "NOSIBLE"
release = "0.4.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_design"
]
add_module_names = False
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "special-members": False,
    "inherited-members": False,
    "show-inheritance": False
}
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_preserve_defaults = True
autosummary_generate = False
autoclass_content = "class"
napoleon_numpy_docstring = True
napoleon_google_docstring = False

html_theme = "sphinx_rtd_theme"
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/tests/*"
]
templates_path = [
    "_templates"
]
html_logo = "_static/logo.svg"
html_theme_options = {
    "logo_only": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "edit",
    "style_nav_header_background": "black",
    "flyout_display": "attached",
    "version_selector": True,
    "language_selector": True,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False
}
html_static_path = [
    "_static"
]
html_favicon = "_static/favicon.ico"
html_css_files = [
    "css/custom.css"
]
html_context = {
    "display_github": True,
    "github_user": "NosibleAI",
    "github_repo": "nosible-py",
    "github_version": "main/docs/"
}
pygments_style = "monokai"


def skip_dunder_and_attrs(
    app: Any,
    what: str,
    name: str,
    obj: Any,
    skip: bool,
    options: Any
) -> Optional[bool]:
    """
    Hide constructors and generated dataclass attributes from member lists.

    :param app: Sphinx application.
    :param what: Documented object category.
    :param name: Member name.
    :param obj: Member object.
    :param skip: Existing skip decision.
    :param options: Autodoc options.
    :return: True to skip, otherwise no override.
    """
    if name == "__init__" or what == "attribute":
        return True
    return None


def setup(
    app: Any
) -> None:
    """
    Register Sphinx callbacks.

    :param app: Sphinx application.
    :return: None.
    """
    app.connect(
        event="autodoc-skip-member",
        callback=skip_dunder_and_attrs
    )
