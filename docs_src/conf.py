# -*- coding: utf-8 -*-
#
# lys_mcp documentation build configuration file.

import sys
import os

sys.path.insert(0, os.path.abspath('../'))

# -- General configuration ------------------------------------------------

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.viewcode']

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'lys_mcp'
copyright = u'2026, Asuka Nakamura'
version = '0.1.0'
release = '0.1.0'

exclude_patterns = ['_build']
pygments_style = 'sphinx'

# -- Options for HTML output ----------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
htmlhelp_basename = 'lys_mcpdoc'
