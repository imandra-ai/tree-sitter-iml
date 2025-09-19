# pyright: basic
# %%
from IPython.core.getipython import get_ipython

ip = get_ipython()
if ip:
    ip.run_line_magic('load_ext', 'autoreload')
    ip.run_line_magic('autoreload', '2')
from collections.abc import Generator
from pathlib import Path
from textwrap import indent
from typing import Any

import tree_sitter_ocaml
from devtools import pformat, pprint, sprint
from rich import print
from rich.markup import escape
from tree_sitter import Language, Node, Parser, Point, Query, QueryCursor

from iml_query import fmt_node, get_parser
from iml_query.format import f1, f2
from iml_query.query import (
    axiom_query,
    decomp_capture_to_req,
    decomp_query,
    eval_node_to_src,
    eval_query,
    extract_decomp_req,
    extract_instance_req,
    extract_opaque_function_names,
    extract_verify_req,
    instance_node_to_req,
    instance_query,
    lemma_query,
    mk_query,
    opaque_query,
    run_query,
    theorem_query,
    top_application_to_decomp,
    verify_node_to_req,
    verify_query,
)
from iml_query.utils import find_pyproject_dir

root_dir = find_pyproject_dir(Path.cwd(), 2)

eg_path = root_dir / 'iml_examples' / 'eg.iml'
eg = eg_path.read_text()

parser = get_parser(ocaml=False)


Node.__repr__ = f1  # type: ignore


# %%
matches = run_query(opaque_query, eg)
matches[0][1]['func_name']

# %%
extract_opaque_function_names(eg)

# %%
extract_verify_req(eg)

# %%
extract_instance_req(eg)

# %%
extract_decomp_req(eg)
