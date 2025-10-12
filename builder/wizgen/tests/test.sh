#!/bin/sh


wizgen/convert.py -i tests/famistudio_asm6.asm   -t asm6   -o tests/fm_asm6.wiz
wizgen/convert.py -i tests/famistudio_ca65.s     -t ca65   -o tests/fm_ca65.wiz
wizgen/convert.py -i tests/famistudio_nesasm.asm -t nesasm -o tests/fm_nesasm.wiz
wizgen/convert.py -i tests/famistudio_sdas.s     -t sdas   -o tests/fm_sdas.wiz

