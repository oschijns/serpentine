#! builder/env/bin/python3

import re
import json
import yaml
import SCons
from SCons.Builder import Builder
from pathlib       import Path
import jinja2


# Specify the compiler, assembler and linker to use
env_sc = SCons.Environment.Environment(
	# C config
	CC      = 'cc65',
	CCFLAGS = ['-I', 'libs/nesdoug', '-I', 'output/gen', '-Oirs', '--add-source', '--cpu', '6502'],

	# ASM config
	AS      = 'ca65',
	ASFLAGS = ['-I', 'libs/nesdoug', '-I', 'output/gen', '-g'],

	# Linker config
	LINK = 'ld65',
	LINKFLAGS = ['-C', 'libs/nesdoug/nrom_32k_vert.cfg'],
)


# Set the output directory
build_directory = Path('output')


# Define the compiler step
compiler = Builder(
    action     = '$CC $CCFLAGS $_CCCOMCOM -o $TARGET $SOURCE',
    src_suffix = '.c',
    suffix     = '.s'
)


# Define the assembler step
assembler = Builder(
    action     = '$AS $ASFLAGS -o $TARGET $SOURCE',
    src_suffix = '.s',
    suffix     = '.o'
)


# Define the linker step
linker = Builder(
    action     = '$LINK $LINKFLAGS -o $TARGET $SOURCES nes.lib',
    src_suffix = '.o',
    suffix     = '.nes'
)


env_sc.Append(BUILDERS = {
    'Compile'  : compiler,
    'Assemble' : assembler, 
    'Link'     : linker
})


# Get the sources both written and generated
sources_j2  = env_sc.Glob('src/*.j2')
sources_c   = env_sc.Glob('src/*.c') + env_sc.Glob('output/gen/*.c')
sources_asm = env_sc.Glob('src/*.s') + env_sc.Glob('output/gen/*.s')
objects = []


# Decompose the source file into its name, extension
regex_j2 = re.compile(r'(\w+)\.(\w+)\.j2$')


# Load Jinja2 templates
loader = jinja2.FileSystemLoader(searchpath = 'src/')
env_j2 = jinja2.Environment(loader = loader)


# Convert templates into sources
for src_j2 in sources_j2:
    print(f'- {src_j2}')

    # check target extension
    m = regex_j2.search(src_j2.name)
    if m is not None:
        name = str(m.group(1))
        ext  = str(m.group(2))
        path = str(build_directory / 'gen' / name)

        # load the template and render it
        template = env_j2.get_template(str(src_j2.name))
        render   = template.render({
            # arbitrary data expected by the template
            'dim': 2, 
            'num': 'fix16', 
            'raw': 'u8', 
            'names': ['x', 'y', 'z', 'w']
        })
        with open(f'{path}_2_fix16.{ext}', 'w') as file:
            file.write(render)


# Compile the sources to assembly scripts
for src_c in sources_c:
    path = str(build_directory / Path(src_c.name).stem)
    print(f'- {src_c}')
    asm = env_sc.Compile (path, src_c)
    obj = env_sc.Assemble(path, asm)
    objects.append(obj)


# Assemble the sources to object files
for src_asm in sources_asm:
    path = str(build_directory / Path(src_asm.name).stem)
    print(f'- {src_asm}')
    obj = env_sc.Assemble(path, src_asm)
    objects.append(obj)


# Link the object files
env_sc.Link('test.nes', objects)
