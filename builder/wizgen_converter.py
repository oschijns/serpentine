#!/usr/bin/env python

"""
    Read an assembly script and convert it to Wiz assembly syntax.
"""


from dataclasses    import dataclass
from configargparse import ArgParser


def main():
    parser = ArgParser(
        prog="wizgen_converter",
        description="Read an assembly script and convert it to Wiz assembly syntax.")

    parser.add_argument('-c', '--config', 
        is_config_file=True,
        help="config file path")

    parser.add_argument('-i', '--input',
        dest='input',
        required=True,
        help="The tileset to convert")

    parser.add_argument('-o', '--output',
        dest='output',
        required=True,
        help="File where to write the binary tileset")

    args   = parser.parse_args()
    config = Config(
        args.inputs, 
        args.output)
    config.run()


# Store configuration for running this script
@dataclass
class Config:
    input  : str
    output : str

    # Run the script
    def run(self):
        wiz_src = ""
        with open(self.output, 'w') as file:
            file.write(wiz_src)



if __name__ == "__main__":
    main()