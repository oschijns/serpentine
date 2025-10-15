#!/usr/bin/python3


import argparse

from processors.utils import proc_line, get_indent
from processors.mos_6502 import Mos6502 


def main() -> None:
    parser = argparse.ArgumentParser(
        prog        = 'convert_to_wiz',
        description = "Read assembly source file and convert it to Wiz source file",
        #epilog      = ""
    )

    # The input file to read from
    parser.add_argument('-i', '--input', 
        type=str, help="The Assembly source to convert")

    # The assembly variant of the input
    # This will also indicate the target platform
    parser.add_argument('-t', '--type',
        type=str, help="The assembly variant of the source file")
    
    # Where to write the output wiz file
    parser.add_argument('-o', '--output',
        type=str, help="Where to write the output wiz source")
    
    # Define a namespace to store the generated sources
    parser.add_argument('-n', '--namespace',
        type=str, default=None, help="Store the generated source in the given namespace")

    args = parser.parse_args()

    # Build a processor to convert the instructions
    processor = Mos6502(args.type)

    # Open both file at once, read and convert line by line
    with open(args.input, 'r') as input, open(args.output, 'w') as output:
        for line in input:
            indent = get_indent(line)
            line = line.strip()

            # handle empty lines
            if not line:
                output.write('\n')

            # handle comments
            elif line.startswith(';'):
                output.write('{{# {} #}}\n'.format(line[1:]))
            
            # TODO replace by Jinja2 templating

            # handle conditional macros
            elif text := proc_line(indent, line, '.ifndef', r'{{% if ({}) is None %}}'):
                output.write(text)

            elif text := proc_line(indent, line, '.ifdef', r'{{% if ({}) is not None %}}'):
                output.write(text)

            elif text := proc_line(indent, line, '.if', r'{{% if {} %}}'):
                output.write(text)
            
            elif text := proc_line(indent, line, '.elseif', r'{{% elif {} %}}'):
                output.write(text)
            
            elif text := proc_line(indent, line, '.else', r'{{% else %}}'):
                output.write(text)

            elif text := proc_line(indent, line, '.endif', r'{{% endif %}}'):
                output.write(text)
            
            elif text := processor.process(indent, line):
                output.write(text)
            
            # Could not process the line
            else: output.write('{{# !!! {} !!! #}}\n'.format(line[1:]))



if __name__ == "__main__":
    main()
