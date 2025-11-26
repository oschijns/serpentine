#!/usr/bin/python3

import numpy
from argparse import ArgumentParser
from music_composer import MusicComposer
from generator_util import generate_wiz


# load a yaml file to constitute a music data
# generate a .wiz file containing sequences of channel data to play
def main():
    parser = ArgumentParser(prog="make_music")

    # input image file to load and process
    parser.add_argument("-i", "--input",
                        dest="partition", 
                        required=True,
                        metavar="FILE", 
                        help="YAML file to process")

    # map generated using metatiles' indexes
    parser.add_argument("-o", "--output",
                        dest="output",
                        required=True,
                        metavar="FILE",
                        help="output .wiz file")

    # read the command line arguments
    args = parser.parse_args()

    # load a music from a YAML file
    composer = MusicComposer()
    composer.load_music(args.partition)

    sequences = []
    generate_wiz(sequences, args.source, 
        namespace="metatiles", comment="Generated sources")


if __name__ == "__main__":
    main()
