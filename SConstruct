#!/usr/bin/env python

import os
import sys
from pathlib import Path

# Set the build directory
build_directory = 'build'

# 6502 compiler step
mos_compiler = Builder(
    action = '$CC $CCFLAGS $_CCCOMCOM -o $TARGET $SOURCE',
    src_suffix = '.c',
    suffix = '.s'
)

# 6502 assembler step
mos_assembler = Builder(
    action = '$AS $ASFLAGS -o $TARGET $SOURCE',
    src_suffix = '.s',
    suffix = '.o'
)

# 6502 linker step
mos_linker = Builder(
    action = '$LINK $LINKFLAGS -o $TARGET $SOURCES nes.lib',
    src_suffix = '.o',
    suffix = '.nes'
)

# Specify the compiler, assembler and linker to use
env = Environment(
	# C config
	CC      = 'cc65',
	CCFLAGS = ['-I', 'include', '-Oirs', '--add-source', '--cpu', '6502'],

	# ASM config
	AS      = 'ca65',
	ASFLAGS = ['-I', 'include', '-I', 'assets', '-g'],

	# Linker config
	LINK = 'ld65',
	LINKFLAGS = ['-C', 'config/nrom_32k_vert.cfg'],
)

env.Append(BUILDERS = {
    'Compile': mos_compiler,
    'Assemble': mos_assembler, 
    'Link': mos_linker
})

# Run the tools
#tools = Glob('tool/*.py')
#import tool.make_src
#tool.make_src.main()

# Get the sources both written and generated
sources_c = Glob('src/*.c') + Glob('gen/*.c')
sources_s = Glob('src/*.s') + Glob('gen/*.s')
objects = []

# Compile the sources to assembly scripts
"""
for c_src in sources_c:
    filename = '{}/{}'.format(build_directory, Path(c_src.name).stem)
    asm = env.Compile(filename, c_src)
    obj = env.Assemble(filename, asm)
    objects.append(obj)
"""
 
# Assemble the sources to object files
for asm in sources_s:
    filename = '{}/{}'.format(build_directory, Path(asm.name).stem)
    obj = env.Assemble(filename, asm)
    objects.append(obj)

# Link the object files
env.Link('test.nes', objects)
