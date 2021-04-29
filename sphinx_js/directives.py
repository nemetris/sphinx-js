"""These are the actual Sphinx directives we provide, but they are skeletal.

The real meat is in their parallel renderer classes, in renderers.py. The split
is due to the unfortunate trick we need here of having functions return the
directive classes after providing them the ``app`` symbol, where we store the
JSDoc output, via closure. The renderer classes, able to be top-level classes,
can access each other and collaborate.

"""
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import flag, unchanged
from sphinx.domains.javascript import JSCallable
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.console import bold

from .renderers import (AutoFunctionRenderer,
                        AutoClassRenderer,
                        AutoNamespaceRenderer,
                        AutoAttributeRenderer,
                        AutoModuleRenderer,
                        AutoModulesRenderer)

logger = logging.getLogger(__name__)
prefix = bold(__('Sphinx-js [Directive]: '))


class JsDirective(Directive):
    """Abstract directive which knows how to pull things out of our IR"""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        'short-name': flag
    }

    def __init__(self, name, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine):
        super().__init__(name, arguments, options, content, lineno,
                            content_offset, block_text, state, state_machine)
        message = 'found {name}:: {arguments}'.format(
            name=name,
            arguments=' '.join(arguments))
        logger.debug(prefix + message)


def auto_function_directive_bound_to_app(app):
    class AutoFunctionDirective(JsDirective):
        """js:autofunction directive, which spits out a js:function directive

        Takes a single argument which is a JS function name combined with an
        optional formal parameter list, all mashed together in a single string.

        """
        def run(self):
            return AutoFunctionRenderer.from_directive(self, app).rst_nodes()

    return AutoFunctionDirective


def auto_class_directive_bound_to_app(app):
    class AutoClassDirective(JsDirective):
        """js:autoclass directive, which spits out a js:class directive

        Takes a single argument which is a JS class name combined with an
        optional formal parameter list for the constructor, all mashed together
        in a single string.

        """
        option_spec = JsDirective.option_spec.copy()
        option_spec.update({
            'members': lambda members: ([m.strip() for m in members.split(',')]
                                        if members else None),
            'exclude-members': _members_to_exclude,
            'private-members': flag})

        def run(self):
            return AutoClassRenderer.from_directive(self, app).rst_nodes()

    return AutoClassDirective

def auto_namespace_directive_bound_to_app(app):
    class AutoNamespaceDirective(JsDirective):
        """js:autonamespace directive, which spits out a js:namespace directive

        Takes a single argument which is a JS class name combined with an
        optional formal parameter list for the constructor, all mashed together
        in a single string.

        """
        option_spec = JsDirective.option_spec.copy()
        option_spec.update({
            'members': lambda members: ([m.strip() for m in members.split(',')]
                                        if members else None),
            'exclude-members': _members_to_exclude,
            'private-members': flag})

        def run(self):
            return AutoNamespaceRenderer.from_directive(self, app).rst_nodes()

    return AutoNamespaceDirective


def auto_attribute_directive_bound_to_app(app):
    class AutoAttributeDirective(JsDirective):
        """js:autoattribute directive, which spits out a js:attribute directive

        Takes a single argument which is a JS attribute name.

        """
        def run(self):
            return AutoAttributeRenderer.from_directive(self, app).rst_nodes()

    return AutoAttributeDirective


def auto_module_directive_bound_to_app(app):
    class AutoModuleDirective(JsDirective):
        """js:automodule directive, which spits out a js:module directive

        Takes a single argument which is a JS module name.

        """
        option_spec = JsDirective.option_spec.copy()
        option_spec.update({
            'members': lambda members: ([m.strip() for m in members.split(',')]
                                        if members else None),
            'exclude-members': _members_to_exclude,
            'private-members': flag})

        def run(self):
            return AutoModuleRenderer.from_directive(self, app).rst_nodes()

    return AutoModuleDirective


def auto_modules_directive_bound_to_app(app):
    class AutoModulesDirective(JsDirective):
        """js:automodules directive, which spits out a toctree to reference
        the generated stub .rst files.
        """
        required_arguments = 0
        optional_arguments = 0
        final_argument_whitespace = False
        has_content = True
        option_spec = JsDirective.option_spec.copy()
        option_spec = {
            'toctree': unchanged,
            # 'nosignatures': flag,
            # 'recursive': flag,
            'template': unchanged,
            'members': lambda members: ([m.strip() for m in members.split(',')]
                                        if members else None),
            'exclude-members': _members_to_exclude,
            'private-members': flag
        }

        def run(self):
            return AutoModulesRenderer.from_directive(self, app).render_toc()

    return AutoModulesDirective


def _members_to_exclude(arg):
    """Return a set of members to exclude given a comma-delim list them.

    Exclude none if none are passed. This differs from autodocs' behavior,
    which excludes all. That seemed useless to me.

    """
    return set(a.strip() for a in (arg or '').split(','))


class JSCustomConstructor(JSCallable):
    """Like a callable but with a different prefix."""
    display_prefix = 'namespace '
    allow_nesting = True


class JSStaticFunction(JSCallable):
    """Like a callable but with a different prefix."""
    display_prefix = 'static '
