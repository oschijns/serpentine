#!.env/bin/python3

"""
    Given a tileset, generate a binary representation (bitplanes).
    ref: https://mrclick.zophar.net/TilEd/download/consolegfx.txt
"""


import sys
import numpy      as np
import imageio.v3 as iio

from numba           import njit, prange
from numpy           import ndarray
from .tileset.system import System
from .tileset.util   import cut_image_into_tiles, reshape_tileset
from dataclasses     import dataclass
from configargparse  import ArgParser


def main():
    parser = ArgParser(
        prog="tile_bitplane",
        description="Generate a binary file to include in a project.")

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

    parser.add_argument('--sys', '--system',
        dest='system',
        required=True,
        choices=System.SYSTEMS,
        help="Generate the tileset for the specified system")

    parser.add_argument('--pal', '--palette',
        dest='palette',
        required=True,
        help="Specify a palette to process the tileset")

    parser.add_argument('--sprite', '--spritesheet',
        dest='is_sprite', 
        default=False,
        action='store_true',
        help="Processing a spritesheet")

    parser.add_argument('--snes-bg-mode',
        dest='snes_bg_mode',
        choices=['2bpp', '4bpp', '8bpp', 'mode7'],
        help="SNES supports multiple background modes")

    args   = parser.parse_args()
    config = Config(
        args.input,
        args.output,
        args.system,
        args.palette,
        args.is_sprite,
        args.snes_bg_mode)
    config.run()


# Store configuration for running this script
@dataclass
class Config:
    input        : str
    output       : str
    system       : str
    palette      : str
    is_sprite    : bool = False
    snes_bg_mode : str | None = None

    # Run the script
    def run(self):
        # Check if the system is known
        system = System.get(self.system, self.is_sprite)
        if system is None:
            print(f"Unrecognized system \"{self.system}\"", file=sys.stderr)
            sys.exit(1)

        # If SNES, check for background mode
        bg_modes = { '2bpp': 2, '4bpp': 4, '8bpp': 8, 'mode7': 8 }
        if self.system == 'snes':
            if self.snes_mode is None:
                print("background mode must be specified for SNES", file=sys.stderr)
                sys.exit(2)
            elif self.snes_mode in bg_modes:
                system.bit_count = bg_modes[self.snes_mode]
                if self.snes_mode == 'mode7':
                    system.use_bitplanes = False
            else:
                print(f"Unrecognized background mode {self.snes_mode}", file=sys.stderr)
                sys.exit(3)

        # Load the images based on the CLI
        image    = iio.imread(self.input)
        palettes = iio.imread(self.palette)

        # Process the data
        serial = process(image, palettes, system)

        # Write the result to the output file
        with open(self.output, 'wb') as file:
            for byte in serial:
                file.write(byte)


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

    @rtype: ndarray (bs) uint8
    @returns: The serialized tileset
    """

    # check the palette
    if not system.check_palette(palettes):
        raise Exception("Provided palette is not compatible with the selected system.")

    # read the image and convert it into an bitplanes
    (tilemap, _) = cut_image_into_tiles(image, palettes, system.tile_size())
    tileset = reshape_tileset(tilemap, system.tileset_shape())
    serial = None

    # Most systems use bitplanes for serialization
    if system.use_bitplanes:
        bitplanes = convert_to_bitplanes(tileset, system.bit_count)

        if system.name == 'nes':
            serial = serial_nes(bitplanes)
        else:
            serial = serial_intertwined(bitplanes, system.intertwined)

    # Mode7 on the SNES use a different serialization strategy
    elif system.name == 'snes':
        serial = serial_snes_mode7(tileset)

    elif system.name == 'md':
        serial = serial_megadrive(tileset)

    # if serialization is properly done, return the buffer
    if serial is None:
        raise Exception("Could not serialize for the target system")
    else:
        return serial





# Convert the tileset into bitplanes to be then serialized into the system's binary format
@njit(fastmath=True)
def convert_to_bitplanes(tileset: ndarray, bit_count: int) -> ndarray:
    """
    Convert the tileset into bitplanes.

    @type  tileset: ndarray (tc, th, tw) uint8
    @param tileset: The tileset to convert into bitplanes

    @type  bit_count: int
    @param bit_count: The number of bitplanes to generate

    @rtype:   ndarray (bc, tc, 8) uint8
    @returns: bitplanes for the provided tileset
    """

    # Get layout
    tile_count = tileset.shape[0]
    tile_h     = tileset.shape[1]
    tile_w     = tileset.shape[2]

    # Allocate a buffer to write the sequence
    bitplanes = np.zeros((bit_count, tile_count, 8), np.uint8)

    # Allocate a buffer to store the bytes being accumulated
    buffer = np.zeros(bit_count, np.uint8)

    # For each tile in the tileset
    for it in prange(tile_count):

        # Convert each row into bytes to be writen in each bitplane
        for ty in prange(tile_h):
            # reset the buffer to zero
            buffer.fill(0)

            # Convert each pixel into bits
            for tx in prange(tile_w):
                index = tileset[it, ty, tx]

                # accumulate the bits into each of the bytes
                # where one byte represent one row of the tile
                for ib in prange(bit_count):
                    byte = buffer[ib]
                    byte <<= 1

                    # mask off all the other bits
                    if (index & (0b1 << ib)) != 0:
                        byte |= 0b1

                    buffer[ib] = byte

            # Store the accumulated bits into the bitplane
            for ib in prange(bit_count):
                bitplanes[ib, it, ty] = buffer[ib]

    # Return the tileset as an image
    return bitplanes



# Serialize bitplanes for NES
@njit(fastmath=True)
def serial_nes(bitplanes: ndarray) -> ndarray:
    """
    Serialize the two bitplanes for usage with the NES

    @type  bitplanes: ndarray (2, th, 8) uint8
    @param bitplanes: The two bitplanes to serialize

    @rtype:   ndarray (bs) uint8
    @returns: array of bytes
    """

    # Allocate the buffer
    bit_count  =   2
    tile_count = 256
    row_count  =   8
    serial = np.zeros(bit_count * tile_count * row_count, np.uint8)

    # Store the data
    for bp in prange(bit_count):
        for it in prange(tile_count):
            for row in prange(row_count):
                index = row + row_count * (bp + bit_count * it)
                serial[index] = bitplanes[bp, it, row]

    return serial



# Serialize bitplanes by intertwining them
# two  by two  for SNES, GameBoy, GameBoy Color and PC-Engine
# four by four for Master System, Game Gear and Wonderswan Color
@njit(fastmath=True)
def serial_intertwined(bitplanes: ndarray, intertwine: int) -> ndarray:
    """
    Serialize the bitplanes by intertwining rows

    @type  bitplanes: ndarray (bc, th, 8) uint8
    @param bitplanes: The bitplanes to serialize

    @type  intertwine: int
    @param intertwine: How many bitplanes should be intertwined

    @rtype:   ndarray (bs) uint8
    @returns: array of bytes
    """

    # Allocate the buffer
    bit_count  = bitplanes.shape[0]
    tile_count = bitplanes.shape[1]
    row_count  = 8
    serial = np.zeros(tile_count * bit_count * row_count, np.uint8)

    # Store the data
    for bp in prange(0, bit_count, intertwine):
        for it in prange(tile_count):
            for row in prange(row_count):

                # intertwine rows two by two or four by four
                index = intertwine * (row + row_count * (it + tile_count * bp))
                for i in prange(intertwine):
                    serial[index + i] = bitplanes[bp + i, it, row]

    return serial


# Serialize a tileset by storing pixels linearly
# 2-bits per pixel for Virtual Boy and NeoGeo Pocket Color
# 4-bits per pixel for Megadrive
# 8-bits per pixel for SNES Mode7
@njit(fastmath=True)
def serial_linear(tileset: ndarray, bit_count: int, swap_byte: bool = False) -> ndarray:
    """
    Serialize the bitplanes linearly

    @type  tileset: ndarray (tc, th, tw) uint8
    @param tileset: The tileset to serialize

    @type  bit_count: int
    @param bit_count: The number of bits per pixel

    @type  swap_byte: bool
    @param swap_byte: Swap the bytes representing a row of a tile

    @rtype:   ndarray (bs) uint8
    @returns: array of bytes
    """

    # Get layout
    tile_count = tileset.shape[0]
    tile_h     = tileset.shape[1]
    tile_w     = tileset.shape[2]

    # Allocate the buffer
    serial = np.zeros(tile_count * 8 * bit_count, np.uint8)
    pix_per_byte = 8 // bit_count
    mask = int(2 ** bit_count) - 1

    # Allocate a buffer to store a row of pixels
    row = np.zeros(bit_count, np.uint8)

    # each tile is (BC * 8) bytes
    for it in prange(tile_count):

        # each row is BC bytes ((BC * 8)-bits integer)
        for ty in prange(tile_h):

            # each pixel is BC bits (8 / BC pixels is 1 byte)
            for tx in prange(0, tile_w, pix_per_byte):

                # accumulate pixels into a byte
                acc = 0
                for i in prange(pix_per_byte):
                    acc = (acc << bit_count) | (tileset[it, ty, tx + i] & mask)

                # where to store the byte in the buffer
                index = tx // pix_per_byte
                row[index] = acc

        # Swap the bytes in the row if necessary
        if swap_byte:
            row = np.flip(row)

        # index = (tx + 8 * (ty + 8 * it)) // pix_per_byte
        index = (ty * 8 + it * 64) // pix_per_byte
        serial[index : index + bit_count] = row

    return serial


# Serialize tileset for SNES mode 7
@njit(fastmath=True)
def serial_snes_mode7(tileset: ndarray) -> ndarray:
    """
    Serialize the tileset for the SNES mode 7

    @type  tileset: ndarray (tc, th, tw) uint8
    @param tileset: The tileset to serialize

    @rtype:   ndarray (bs) uint8
    @returns: array of bytes
    """

    # Get layout
    tile_count = tileset.shape[0]
    tile_h     = tileset.shape[1]
    tile_w     = tileset.shape[2]

    # Allocate the buffer
    serial = np.zeros(tile_count * 8 * 8, np.uint8)

    # each tile is 64 bytes
    for it in prange(tile_count):

        # each row is 8 bytes (64-bits integer)
        for ty in prange(tile_h):

            # each pixel is 8 bits (1 pixel is 1 byte)
            for tx in prange(tile_w):
                index = tx + ty * 8 + it * 64
                serial[index] = tileset[it, ty, tx]

    return serial


# Serialize a tileset for the Megadrive
@njit(fastmath=True)
def serial_megadrive(tileset: ndarray) -> ndarray:
    """
    Serialize the tileset for the megadrive

    @type  tileset: ndarray (tc, th, tw) uint8
    @param tileset: The tileset to serialize

    @rtype:   ndarray (bs) uint8
    @returns: array of bytes
    """

    # Get layout
    tile_count = tileset.shape[0]
    tile_h     = tileset.shape[1]
    tile_w     = tileset.shape[2]

    # Allocate the buffer
    serial = np.zeros(tile_count * 4 * 8, np.uint8)

    # each tile is 32 bytes
    for it in prange(tile_count):

        # each row is 4 bytes (32-bits integer)
        for ty in prange(tile_h):

            # each pixel is 4 bits (2 pixels is 1 byte)
            for tx in prange(0, tile_w, 2):

                # store two pixels in a single byte
                pix0 = tileset[it, ty, tx + 0] & 0b1111
                pix1 = tileset[it, ty, tx + 1] & 0b1111

                # where to store the byte in the serialized buffer
                index = (tx // 2) + ty * 4 + it * 32
                serial[index] = (pix0 << 4) | pix1

    return serial


if __name__ == '__main__':
    main()