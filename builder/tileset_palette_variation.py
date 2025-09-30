#!/usr/bin/env python

"""
    Given a tileset, generate variation based on the number of palettes available on the target system.
"""

import sys
import imageio.v3 as iio

from argparse import ArgumentParser
from numpy    import ndarray

from util.tileset_system import System
from util.tileset_util   import cut_image_into_tiles, reshape_tileset, reformat_tileset


def main():
    parser = ArgumentParser(
        prog="tileset_palette_variation",
        description="Generate tile variations based on the number of palettes available.")

    parser.add_argument('-i', '--input', 
        dest='input', 
        required=True, 
        help="The tileset to make variations of")
    
    parser.add_argument('-o', '--output',
        dest='output',
        required=True,
        help="File where to write the generated tileset variations")

    parser.add_argument('--sys', '--system',
        dest='system',
        required=True,
        choices=System.SYSTEMS,
        help="Generate tileset variations compatible with the specified system")
    
    parser.add_argument('--pal', '--palette',
        dest='palettes',
        required=True,
        help="Specify which variations to generate")

    parser.add_argument('--sprite', '--spritesheet',
        dest='is_sprite', 
        default=False,
        action='store_true',
        help="Processing a spritesheet")

    args = parser.parse_args()

    # Check if the system is known
    system = System.get(args.system, args.is_sprite)
    if system is None:
        print(f"Unrecognized system \"{args.system}\"", file=sys.stderr)
        sys.exit(1)

    # Load the images based on the CLI
    image    = iio.imread(args.input)
    palettes = iio.imread(args.palettes)

    # Process the data
    tileset = process(image, palettes, system)
    iio.imwrite(args.output, reformat_tileset(tileset, palettes, pal_variation=True))



# Process the data
def process(image: ndarray, palettes: ndarray, system: System) -> ndarray:
    """
    Use the provided images to generate a tileset

    @type  image: ndarray (ih, iw, 3) uint8
    @param image: The pixel art to extract tiles from

    @type  palettes: ndarray (pc, ps, 3) uint8
    @param palettes: Palettes provided

    @type  system: System
    @param system: Target system configuration

    @rtype: ndarray (tc, th, tw) uint8
    @returns: The processed tileset
    """

    # check the palette
    if not system.check_palette(palettes):
        raise Exception("Provided palette is not compatible with the selected system.")

    # read the image and convert it into an indexed tileset
    (tilemap, _) = cut_image_into_tiles(image, palettes, system.tile_size())
    return reshape_tileset(tilemap, system.tileset_shape())



if __name__ == '__main__':
    main()