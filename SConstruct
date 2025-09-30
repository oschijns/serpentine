#! builder/env/bin/python3

import SCons
from SCons.Builder import Builder
from pathlib       import Path
import jinja2


# Specify the compiler, assembler and linker to use
env_s = SCons.Environment.Environment(
	# C config
	CC      = 'cc65',
	CCFLAGS = ['-I', 'libs/nesdoug', '-Oirs', '--add-source', '--cpu', '6502'],

	# ASM config
	AS      = 'ca65',
	ASFLAGS = ['-I', 'libs/nesdoug', '-g'],

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


env_s.Append(BUILDERS = {
    'Compile'  : compiler,
    'Assemble' : assembler, 
    'Link'     : linker
})


# Get the sources both written and generated
sources_j2_c   = env_s.Glob('src/*.c.j2')
sources_j2_asm = env_s.Glob('src/*.s.j2')
sources_c      = env_s.Glob('src/*.c') + env_s.Glob('output/gen/*.c')
sources_asm    = env_s.Glob('src/*.s') + env_s.Glob('output/gen/*.s')
objects = []


#env_j = jinja2.Environment(
#    loader = jinja2.PackageLoader('snaker')
#)


# Convert templates into sources
for src_j2 in sources_j2_c:
    path = str(build_directory / Path(src_j2.name).stem)
    print(f'- {src_j2}')


# Convert templates into sources
for src_j2 in sources_j2_asm:
    path = str(build_directory / Path(src_j2.name).stem)
    print(f'- {src_j2}')


# Compile the sources to assembly scripts
for src_c in sources_c:
    path = str(build_directory / Path(src_c.name).stem)
    print(f'- {src_c}')
    asm = env_s.Compile (path, src_c)
    obj = env_s.Assemble(path, asm)
    objects.append(obj)


# Assemble the sources to object files
for src_asm in sources_asm:
    path = str(build_directory / Path(src_asm.name).stem)
    print(f'- {src_asm}')
    obj = env_s.Assemble(path, src_asm)
    objects.append(obj)


# Link the object files
env_s.Link('test.nes', objects)
