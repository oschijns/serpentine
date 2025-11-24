"""
    Builder for jinja templates
"""

import re
from pathlib           import Path
from logging           import Logger
from SCons.Builder     import Builder
from SCons.Environment import Environment


# Compile a wiz project
class WizBuilder:

    # Identify the target system based on the ROM extension
    _ROM_FILE = re.compile(r'(?P<name>\S+)\.(?P<ext>\w+)$')

    # Initialize the wiz builder with a configuration
    def __init__(self,
        root_dir     : Path,
        logger       : Logger,
        rom_name     : str,
        target_system: str = '',
    ):
        """
        Compile a wiz project

        @type  root_dir: Path
        @param root_dir: The root directory of the project

        @type  logger: Logger
        @param logger: The logger to report on build status

        @type  rom_name: str
        @param rom_name: The name of the output ROM file

        @type  target_system: str
        @param target_system: The target system to build for
        """

        self.root_dir: Path   = root_dir
        self.logger  : Logger = logger
        self.rom_name: str    = rom_name
        self.system  : str    = target_system.lower()

        # Get the rom extension
        m = self._JINJA_FILE.search(rom_name)
        if m is None:
            raise Exception(f'Could not identify the ROM extension {rom_name}')
        ext: str = m.group('ext')

        # If target system was not set, use the rom extension
        if self.system == '':
            self.system = ext

        # If we are compiling a SNES project, we have two compilation steps instead of one
        self.is_snes: bool = False

        if self.system in ['c64', 'nes', 'appleII', 'a2600', 'a5200', 'a7800']:
            cpu = '6502'
        elif self.system in ['pce']:
            cpu = 'huc6280'
        elif self.system == ['sms', 'gg', 'msx', 'zx']:
            cpu = 'z80'
        elif self.system == ['gb', 'gbc']:
            cpu = 'gb'
        elif self.system == 'snes':
            cpu = 'wdc65816'
            self.is_snes = True
        else:
            raise ValueError(f'Unsupported target system: {target_system}')

        # Define where to look for templates and where to output rendered sources
        dir_main  = str(self.root_dir / 'src')
        dir_gen   = str(self.root_dir / 'target' / 'source')
        dir_cache = str(self.root_dir / 'target' / 'cache')

        # Define environment variables
        self.env: Environment = Environment(WIZ = 'wiz')
        compiler = Builder(
            action     = f'$WIZ $WIZ_FLAGS -I{dir_main} -I{dir_gen} -I{dir_cache} --system={cpu} -o $TARGET $SOURCE',
            src_suffix = '.wiz',
            suffix     = f'.{ext}'
        )
        self.env.Append(BUILDERS = {'Compile': compiler})

        # If the target is the SNES, there is an extra step to 
        # compile the program specific to the SPC700 sound chip.
        if self.is_snes:
            dir_main  = str(self.root_dir / 'src_audio')
            dir_gen   = str(self.root_dir / 'target' / 'source_audio')
            target    = str(self.root_dir / 'target' / 'cache' / 'spc_main.bin')

            compiler_audio = Builder(
                action     = f'$WIZ $WIZ_AUDIO_FLAGS -I{dir_main} -I{dir_gen} -I{dir_cache} --system=spc700 -o {target} $SOURCE',
                src_suffix = '.wiz',
                suffix     = '.bin'
            )
            self.env.Append(BUILDERS = {
                'Compile'     : compiler,
                'CompileAudio': compiler_audio
            })



    # Compile, assemble and link all sources found in the project
    def compile_sources(self):
        if self.is_snes:
            self._compile_sources('src_audio', 'CompileAudio')
        self._compile_sources('src', 'Compile')



    # Compile a WIZ source file
    def _compile_sources(self, source: str, step: str):
        file_in  = str(self.root_dir / source   / 'main.wiz')
        file_out = str(self.root_dir / 'target' / 'cache' / 'spc_main.bin')
        self.env['step'](file_out, file_in)
        self.logger.info(f'Compiled {file_in}')