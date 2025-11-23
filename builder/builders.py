"""
    Define a set of builders for generating a ROM from scratch.
    A project should have the following structure:
    ```
    root:
        assets: (.png, .json, .txt)
        scripts: (.py)
        src: (.h, .c, .s, .wiz, .j2)
        target: generated files
    ```
    
    Load a manifest file in YAML format:
    ```yaml
    ---
    target_system: nes
    output_rom: my_game.nes
    source_type: c
    c_toolchain:
        compiler:  cc65
        assembler: ca65
        linker:    ld65
        compiler_flags:  ['-Oirs', '--add-source']
        assembler_flags: ['-g']
        linker_flags:    ['-C', 'libs/nesdoug/nrom_32k_vert.cfg']
    librairies:
        - nesdoug
    templates:
        - my_template.h.j2
    features:
        some_feature: true
    ```
"""

import re
import os
import glob
import logging
import yaml
import SCons
import jinja2
from pathlib import Path


# Define a process for building a serpentine project
class Builder:

    # Identify a template file name and extract relevant informations
    _JINJA_FILE = re.compile(r'(?P<name>\S+)\.(?P<ext>\w+)\.j2$')

    # Identify the extension from the output ROM name
    _ROM_EXT = re.compile(r'(?P<name>\S+)\.(?P<ext>\w+)$')

    # Load a YAML manifest file
    def __init__(self, manifest_path: str, log: int = logging.INFO):
        """
        Create a builder to convert assets, templates and sources into a functional ROM
        """

        # Get the root of the project
        self.main_dir: Path = Path(os.path.dirname(os.path.realpath(manifest_path)))

        # Create a logger to report on build status
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename = self.main_dir / 'status.log', level = log)

        # Load the manifest and extract relevant data
        with open(manifest_path, 'r') as file:
            manifest = yaml.load(file)

            self.system     : str       = manifest['target_system']
            self.output_rom : str       = manifest['output_rom']
            self.librairies : list[str] = manifest['librairies'] or []
            self.templates  : list[str] = manifest['templates' ] or []
            self.features   : dict      = manifest['features'  ] or {}

            # Given the source type, 
            stype: str = manifest['source_type']
            if stype == 'c':
                libs: list[str] = ['-I', str(self.main_dir / 'target' / 'source')]
                for lib in self.librairies:
                    libs.append('-I')
                    libs.append(str(self.main_dir / 'libs' / lib))

                cdata  : dict = manifest['c_toolchain']
                dir_lib: Path = self.main_dir / 'libs'
                dir_gen: Path = self.main_dir / 'target' / 'source'

                # build an environment
                comp: str = cdata['compiler' ]
                assm: str = cdata['assembler']
                link: str = cdata['linker'   ]
                comp_f: list[str] = cdata['compiler_flags' ] + libs
                assm_f: list[str] = cdata['assembler_flags'] + libs
                link_f: list[str] = cdata['linker_flags'   ]
                self.env = SCons.Environment.Environment(
                    CC   = comp, CCFLAGS   = comp_f,
                    AS   = assm, ASFLAGS   = assm_f,
                    LINK = link, LINKFLAGS = link_f,
                )

                m = Builder._ROM_EXT.search(self.output_rom)
                if m is None:
                    raise Exception(f"Could not identify extension for output rom file {self.output_rom}")
                extension = m.group('ext')

                # Define the three step for building the sources
                comp_s = SCons.Builder.Builder(
                    action     = '$CC $CCFLAGS $_CCCOMCOM -o $TARGET $SOURCE',
                    src_suffix = '.c',
                    suffix     = '.s'
                )
                assm_s = SCons.Builder.Builder(
                    action     = '$AS $ASFLAGS -o $TARGET $SOURCE',
                    src_suffix = '.s',
                    suffix     = '.o'
                )
                link_s = SCons.Builder.Builder(
                    action     = '$LINK $LINKFLAGS -o $TARGET $SOURCE',
                    src_suffix = '.o',
                    suffix     = f'.{extension}'
                )

                # Add the build steps to the environment
                self.env.Append(BUILDERS = {
                    'Compile'  : comp_s,
                    'Assemble' : assm_s, 
                    'Link'     : link_s
                })
            elif stype == ' wiz':
                pass
            


        # Find all jinja files in src (and in target) 
        # and generate corresponding sources
        def convert_jinja(self):
            # Define the two paths to look for jinja templates
            dir_src: Path = self.main_dir / 'src'
            dir_gen: Path = self.main_dir / 'target' / 'jinja'
            dir_out: Path = self.main_dir / 'target' / 'source'

            # We try to look up for files in `src` and `target/jinja`
            #root_dir = str(self.main_dir)
            #files = (
            #    glob.glob(str(src_main / '**' / '*.j2'), root_dir = root_dir, recursive = True) +
            #    glob.glob(str(src_gen         / '*.j2'), root_dir = root_dir))

            # Define the filesystem
            loader = jinja2.FileSystemLoader([str(dir_src), str(dir_gen)])
            env    = jinja2.Environment(loader = loader)
            for file in self.templates:
                # identify the file name
                m = Builder._JINJA_FILE.search(file)
                if m is not None:
                    name: str = m.group('name')
                    ext : str = m.group('ext')

                    out_path: str = str(dir_out / f'{name}.{ext}')
                    with open(out_path, 'w') as out_file:
                        temp = env.get_template(file)
                        rend = temp.render(self.features)
                        out_file.write(rend)
                        self.logger.info(f'rendered "{out_path}"')


