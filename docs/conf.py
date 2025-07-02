import os, sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'Nosible Client'
copyright = '2025, Richard Taylor'
author = 'Richard Taylor'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
]

add_module_names = False
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "special-members": False,
    "inherited-members": False,
    "show-inheritance": False,
    "exclude-members": "FIELDS,__init__,__enter__,Nosible.__exit__()",
}
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_preserve_defaults = True

autosummary_generate = True
napoleon_numpy_docstring = True
napoleon_google_docstring = False

html_theme = "sphinx_rtd_theme"
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**/tests/*']

templates_path = ['_templates']

html_logo = '_static/logo.svg'

html_theme_options = {
    'logo_only': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': 'black',
    'flyout_display': 'attached',
    'version_selector': True,
    'language_selector': True,
    # Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    'display_version': True,
}

html_static_path = ['_static']

html_favicon = "_static/favicon.ico"

html_css_files = [
    'css/custom.css',
]

pygments_style = "monokai"

def skip_all_dunders(app, what, name, obj, skip, options):
    """Tell autodoc & autosummary to ignore __dunder__ members."""
    if name.startswith("__") and name.endswith("__"):
        return name
    return None

def setup(app):
    app.connect("autodoc-skip-member", skip_all_dunders)