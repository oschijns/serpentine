"""
    Builder for jinja templates
"""

import re
from pathlib import Path
from logging import Logger
from typing  import Any, Callable
from jinja2  import Environment, FileSystemLoader


# Read a list of jinja files and render them into sources for the next steps
class JinjaBuilder:

    # Identify a template file name and extract relevant informations
    _JINJA_FILE = re.compile(r'(?P<name>\S+)\.(?P<ext>\w+)\.j2$')

    # Initialize the jinja builder with a configuration
    def __init__(self,
        root_dir : Path,
        logger   : Logger,
        source   : str = 'src',
        target   : str = 'source'
    ):
        """
        Create a jinja builder to render templates into source files

        @type  root_dir: Path
        @param root_dir: The root directory of the project

        @type  logger: Logger
        @param logger: The logger to report on build status

        @type  source: str
        @param source: Surcharge the location where to read user's scripts

        @type  target: str
        @param target: Surcharge the location where to write rendered scripts
        """

        self.root_dir: Path   = root_dir
        self.logger  : Logger = logger

        # Define where to look for templates and where to output rendered sources
        self.dir_input    : Path = self.root_dir / source
        self.dir_generated: Path = self.root_dir / 'target' / 'templates'
        self.dir_output   : Path = self.root_dir / 'target' / target

        # Create the jinja environment
        loader: FileSystemLoader = FileSystemLoader([
            str(self.dir_input),
            str(self.dir_generated)
        ])
        self.env: Environment = Environment(loader = loader)


    # Register a python function to be used in Jinja templates
    def register_function(self, name: str, func: Callable):
        self.env.globals[name] = func


    # Render a jinja template into a source file
    def render(self, temp_path: Path, config: dict[str, Any] = {}, is_generated: bool = False):
        """
        Render a jinja template into a source file

        @type  files: list[Path]
        @param files: The list of jinja template files to process

        @type  config: dict[str, Any]
        @param config: The configuration data to use when rendering templates

        @type  is_generated: bool
        @param is_generated: Whether the template is located in the generated templates folder
        """

        # Check target extension
        m = self._JINJA_FILE.search(temp_path.name)
        if m is None:
            raise Exception(f'Invalid jinja template file name: {temp_path.name}')

        # Where is the file located and where the render should go
        path_in : Path = (self.dir_generated if is_generated else self.dir_input) / temp_path
        path_out: Path = self.dir_output / f"{m.group('name')}.{m.group('ext')}"

        # Load the template and render it
        temp   = self.env.get_template(str(path_in))
        render = temp.render(config)

        # Write the rendered file to disk
        with open(path_out, 'w') as file:
            file.write(render)

        # Log the rendering
        self.logger.info(f'rendered "{path_out}"')
