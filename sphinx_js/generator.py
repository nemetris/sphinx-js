import os
import re
from typing import List, NamedTuple, Tuple

from sphinx.application import Sphinx
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.console import bold
from sphinx.util.osutil import ensuredir

from .renderers import AutoModulesRenderer


logger = logging.getLogger(__name__)
prefix = bold(__('Sphinx-js [Automodules]: '))

AutomodulesEntry = NamedTuple('AutomodulesEntry', [('name', str),
                                                   ('path', str),
                                                   ('members', str),
                                                   ('exclude_members', str),
                                                   ('private_members', str)])


def process_automodules(app: Sphinx) -> None:
    env = app.builder.env
    sources = [env.doc2path(x, base=None) for x in env.found_docs
                if os.path.isfile(env.doc2path(x))]

    if not sources:
        return

    suffix = get_rst_suffix(app)
    if suffix is None:
        logger.warning(prefix + 'automodules generats .rst files internally. '
                          'But your source_suffix does not contain .rst. Skipped.')
        return

    generate_automodules_docs(
        sources,
        suffix=suffix,
        base_path=app.srcdir,
        app=app,
        overwrite=True,
        encoding=app.config.source_encoding)


# -- Generating output ---------------------------------------------------------

def generate_automodules_docs(sources: List[str],
                              suffix: str = '.rst',
                              base_path: str = None,
                              app: Sphinx = None,
                              overwrite: bool = True,
                              encoding: str = 'utf-8') -> None:

    showed_sources = list(sorted(sources))
    if len(showed_sources) > 20:
        showed_sources = showed_sources[:10] + ['...'] + showed_sources[-10:]
    logger.info(prefix + 'generating automodules for: %s' % ', '.join(showed_sources))

    if base_path is not None:
        sources = [os.path.join(base_path, filename) for filename in sources]

    template = AutoModulesRenderer(None, app, arguments=['dummy'])
    analyzer = app._sphinxjs_analyzer

    # read
    items = find_automodules_in_files(sources)

    # write
    app.generated_automodules_docs = []
    for entry in sorted(set(items), key=str):
        path = os.path.abspath(entry.path)
        ensuredir(path)

        # get a list of modules as ir by given automodules entry
        modules = analyzer.resolve_name(entry.name)

        # iterate through all js modules
        for module in modules:
            # skip generation of stub file
            if module.name in entry.exclude_members:
                continue

            # render template
            content = template.rst([module.name], entry, use_short_name=True)

            filename = os.path.join(path, module.name + suffix)
            if os.path.isfile(filename):
                with open(filename, encoding=encoding) as f:
                    old_content = f.read()

                if content == old_content:
                    app.generated_automodules_docs.append((filename, path, module.name, suffix))
                    logger.info(prefix + 'automodule stub file {}{} is already up-to-date'.format(
                                module.name, suffix))
                    continue
                elif overwrite:  # content has changed
                    with open(filename, 'w', encoding=encoding) as f:
                        f.write(content)
            else:
                with open(filename, 'w', encoding=encoding) as f:
                    f.write(content)
            app.generated_automodules_docs.append((filename, path, module.name, suffix))
            logger.info(prefix + 'generated automodule stub file: {}{}'.format(
                module.name, suffix))


# -- Finding documented entries in files ---------------------------------------
def find_automodules_in_files(filenames: List[str]) -> List[AutomodulesEntry]:
    """Find out what items are documented in source/*.rst.

    See `find_automodules_in_lines`.
    """
    documented = []  # type: List[AutomodulesEntry]
    for filename in filenames:
        with open(filename, encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
            documented.extend(find_automodules_in_lines(lines, filename=filename))
    return documented


def find_automodules_in_lines(lines: List[str], module: str = None, filename: str = None
                              ) -> List[AutomodulesEntry]:
    """Find out what items appear in automodules:: directives in the
    given lines.

    Returns a list of (name, toctree, caption, members, exclude-members, private-members)
    where *name* is a name of an object and *toctree* the :toctree: path
    of the corresponding automodules directive (relative to the root of the file name).
    *toctree* ``None`` if the directive does not have the corresponding options set.
    """
    automodules_re = re.compile(r'^(\s*)\.\.\s+js:automodules::\s*')
    automodules_item_re = re.compile(r'^\s+(~?[_a-zA-Z][a-zA-Z0-9_./]*)\s*.*?')
    toctree_arg_re = re.compile(r'^\s+:toctree:\s*(.*?)\s*$')
    members_arg_re = re.compile(r'^\s+:members:\s*(.*?)\s*$')
    exclude_members_arg_re = re.compile(r'^\s+:exclude-members:\s*(.*?)\s*$')
    private_members_arg_re = re.compile(r'^\s+:private-members:\s*(.*?)\s*$')

    documented = []  # type: List[AutomodulesEntry]

    toctree = None  # type: str
    members = None
    exclude_members = ''
    private_members = False
    in_automodules = False
    base_indent = ''

    for line in lines:
        if in_automodules:
            m = toctree_arg_re.match(line)
            if m:
                toctree = m.group(1)
                if filename:
                    toctree = os.path.join(os.path.dirname(filename),
                                           toctree)
                continue

            m = members_arg_re.match(line)
            if m:
                members = m.group(1).strip()
                continue

            m = exclude_members_arg_re.match(line)
            if m:
                exclude_members = m.group(1).strip()
                continue

            m = private_members_arg_re.match(line)
            if m:
                private_members = m.group(1).strip()
                continue

            if line.strip().startswith(':'):
                continue  # skip options

            m = automodules_item_re.match(line)
            if m:
                name = m.group(1).strip()
                documented.append(AutomodulesEntry(name, toctree, members, exclude_members, private_members))
                continue

            if not line.strip() or line.startswith(base_indent + ' '):
                continue

            in_automodules = False

        m = automodules_re.match(line)
        if m:
            in_automodules = True
            base_indent = m.group(1)
            toctree = '_automodules'
            members = None
            exclude_members = ''
            private_members = None
            continue

    return documented


def get_rst_suffix(app: Sphinx) -> str:
    def get_supported_format(suffix: str) -> Tuple[str, ...]:
        parser_class = app.registry.get_source_parsers().get(suffix)
        if parser_class is None:
            return ('restructuredtext',)
        return parser_class.supported

    suffix = None  # type: str
    for suffix in app.config.source_suffix:
        if 'restructuredtext' in get_supported_format(suffix):
            return suffix

    return None
