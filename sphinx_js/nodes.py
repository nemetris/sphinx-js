from docutils import nodes
from docutils.nodes import Node


class automodulestoctree(nodes.comment):
    pass

def automodules_noop(self: nodes.NodeVisitor, node: Node) -> None:
    pass

def automodules_toc_visit_html(self: nodes.NodeVisitor, node: automodulestoctree) -> None:
    """Hide automodules toctree list in HTML output."""
    raise nodes.SkipNode
