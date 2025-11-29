#!.env/bin/python3

"""
    Read pixel art images and try to identify identical tiles.
    Given a profile parameter, this script will optimize tile packing for various retro consoles.
    It is not intended to be used to create actual maps.
    Thus the input pixel art should be seen as an example of the type of scenes, you want to create.
    And the actual tile work should be done in a proper tilemap software such as Tiled.
"""

import sys
import numpy      as np
import imageio.v3 as iio

from numpy           import ndarray
from tileset.system  import System
from tileset.util    import cut_image_into_tiles, reformat_tileset, extract_tileset
from dataclasses     import dataclass
from configargparse  import ArgParser


def main():
    parser = ArgParser(
        prog="tileset_packer_tilemap",
        description="Process pixel art images to identify common tiles and output a tileset.")

    parser.add_argument('-c', '--config', 
        is_config_file=True,
        help="config file path")

    parser.add_argument('-i', '--input', 
        dest='inputs',
        nargs='+',
        required=True, 
        help="Pixel art image(s) to process")
    
    parser.add_argument('-o', '--output',
        dest='output',
        required=True,
        help="File where to write the generated tileset")

    parser.add_argument('--sys', '--system',
        dest='system',
        required=True,
        choices=System.SYSTEMS,
        help="Generate a tileset compatible with the specified system")
    
    parser.add_argument('--pal', '--palette',
        dest='palette',
        required=True,
        help="Specify the order of the colors")

    parser.add_argument('--charset',
        dest='charset',
        default=None,
        help="Reserve space in the generated tileset to store the provided charset")
    
    parser.add_argument('--charset-offset',
        dest='charset_offset',
        default=0,
        help="First index where to store the provided charset")

    parser.add_argument('--charset-size',
        dest='charset_size',
        default=-1,
        help="Number of characters defined in the charset")

    args = parser.parse_args()

    # Should we include a character set in the tilemap
    charset = None
    if args.charset is not None:
        charset = (args.charset, int(args.charset_offset), int(args.charset_size))

    config = Config(
        args.inputs,
        args.output,
        args.system,
        args.palette,
        charset)
    config.run()


# Store configuration for running this script
@dataclass
class Config:
    inputs  : list[str]
    output  : str
    system  : str
    palette : str
    charset : tuple[str, int, int] | None = None

    # Run the script
    def run(self):
        # Check if the system is known
        system = System.get(self.system)
        if system is None:
            print(f"Unrecognized system \"{self.system}\"", file=sys.stderr)
            sys.exit(1)

        # Load the images based on the CLI
        images = []
        for input in self.inputs:
            images.append(iio.imread(input))
        palettes = iio.imread(self.palette)

        # Check if a character set was provided
        charset = None
        if self.charset is not None:
            charset = (iio.imread(self.charset[0]), self.charset[1], self.charset[2])

        # Process the provided data
        # TODO: write the tilemaps to a json file?
        (tileset, _) = process(images, palettes, system, charset)

        # Reformat the tileset into an image
        iio.imwrite(self.output, reformat_tileset(tileset, palettes))


# Process the data
def process(
    images   : list[ndarray], 
    palettes : ndarray,
    system   : System,
    charset  : tuple[ndarray, int, int] | None,
    ) -> tuple[ndarray, list[ndarray]]:
    """
    Use the provided images to generate a tileset

    @type  images: list( ndarray (ih, iw, 3) uint8 )
    @param images: The pixel arts to extract tiles from

    @type  palettes: ndarray (pc, ps, 3) uint8
    @param palettes: Palettes provided

    @type  system: System
    @param system: Target system configuration

    @type  charset: optional( ndarray (ch, cw, 3) uint8, int )
    @param charset: Optional character set to include at the given offset

    @rtype: (ndarray (tc, th, tw) uint8, ndarray (mh, mw, 3) uint16)
    @returns: The processed tileset and the tilemap as indexes
    """

    # check the palette
    if not system.check_palette(palettes):
        raise Exception("Provided palette is not compatible with the selected system.")

    # Allocate a buffer to store the generated tileset
    tileset    = np.zeros(system.tileset_shape(), np.uint8)
    used_tiles = np.zeros(system.tile_count, np.bool)

    # Check if a charset was provided and should be processed first
    if charset is not None:

        # cut the charset into individual tiles
        (char_map, char_offset, char_size) = charset
        (char_map, _) = cut_image_into_tiles(char_map, palettes, system.tile_size())
        char_end = char_offset + (
            char_size if char_size > -1 else char_map.shape[0] * char_map.shape[1])

        # iterate over the character map and store the tiles into the tileset
        for iy, ix in np.ndindex(char_map.shape[:2]):
            # write characters into the tileset until we reach the last character
            if char_offset >= char_end:
                break
            tileset   [char_offset] = char_map[iy, ix]
            used_tiles[char_offset] = True
            char_offset += 1

    # Process the actual images
    results = []
    for image in images:
        (tile_map, pal_map) = cut_image_into_tiles(image, palettes, system.tile_size())
        results.append(extract_tileset(tile_map, pal_map, system.flipping(), tileset, used_tiles))

    # We return the optimized tileset and the tilemap made of indexes
    return (tileset, results)



if __name__ == '__main__':
    main()