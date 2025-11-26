#!/usr/bin/python3

import numpy
from argparse import ArgumentParser
from tileset_loader import TileSetLoader
from generator_util import generate_wiz


# load one or two images to constitute a tileset
# the first image define the metatiles
# the second image define the alphabet (optional)
# generate a .chr file containing the tileset
# generate a .bin file containing the metatiles definitions
# generate a .wiz file containing sequences of metatiles indexes
def main():
    parser = ArgumentParser(prog="make_tiles")

    # input image file to load and process
    parser.add_argument("-i", "--input",
                        dest="image", 
                        required=True,
                        metavar="FILE", 
                        help="input image to process")

    # optional font file
    parser.add_argument("-f", "--font",
                        dest="font",
                        required=False,
                        metavar="FILE",
                        default=None,
                        help="input font to store tiles in the tile set")

    # output tileset generated
    parser.add_argument("-t", "--tileset",
                        dest="tileset",
                        required=True,
                        metavar="FILE",
                        help="output .chr file")

    # output metatiles generated
    parser.add_argument("-m", "--metatiles",
                        dest="metatiles",
                        required=True,
                        metavar="FILE",
                        help="output .bin file")

    # map generated using metatiles' indexes
    parser.add_argument("-s", "--source",
                        dest="source",
                        required=True,
                        metavar="FILE",
                        help="output .wiz file")

    # read the command line arguments
    args = parser.parse_args()

    # load an image to constitute a tileset
    loader = TileSetLoader()
    loader.load_fontset(args.font)
    tilemap, _ = loader.load_tileset(args.image)

    # group up 4x4 tiles into metatiles
    metatilemap, metatiles = compose_metatiles(tilemap)

    # write the tileset CHR file
    loader.serialize_to_chr(args.tileset)

    # write the metatiles binary file
    serialize_metatiles(metatiles, args.metatiles)

    # write the metatilemap into a source file
    sequences = []
    for y in range(metatilemap.shape[1]):
        sequences.append(metatilemap[:, y])
    generate_wiz(sequences, args.source, 
        namespace="metatiles", comment="Generated sources")


# group up 4x4 tiles into metatiles
def compose_metatiles(tilemap):

    # check the dimensions of the tilemap
    width, height, _ = tilemap.shape
    if width % 4 != 0 or height % 4 != 0:
        raise Exception("Input data is not a multiple of 4×4.")
    width  //= 4
    height //= 4

    # transform the tilemap into a metatilemap
    metatilemap = numpy.zeros((width, height), dtype=numpy.uint8)

    # create a list to store the metatiles
    metatiles = []

    # iterate over each metatile
    for metatile_x, metatile_y in numpy.ndindex(width, height):
        x = metatile_x * 4
        y = metatile_y * 4

        # extract the metatile
        metatile = tilemap[x:x+4, y:y+4]
        tiles    = metatile[:, :, 0]
        palettes = metatile[:, :, 1]

        # compose the palette mask for the metatile
        palette_mask = 0b00000000
        for index, (sub_y, sub_x) in enumerate(numpy.ndindex(2, 2)):
            sx = sub_x * 2
            sy = sub_y * 2

            # check that each square of 2x2 tiles contains the same color
            palette = palettes[sx, sy]
            if not (palette == palettes[sx+1, sy] == palettes[sx, sy+1] == palettes[sx+1, sy+1]):
                raise Exception("Groups of 2×2 tiles must use the same palette.")

            # add the palette to the palette mask
            palette_mask |= palette << (index * 2)

        # compose the metatile
        metatile = numpy.append(tiles.ravel(), palette_mask)

        # check if this metatile pattern already exists
        try:
            index = metatiles.index(metatile)
        except ValueError:
            index = len(metatiles)
            metatiles.append(metatile)

        # store the metatile in the metatilemap
        metatilemap[metatile_x, metatile_y] = index

    # check that the number of metatiles generated is sane
    nb_metatiles = len(metatiles)
    if nb_metatiles > 0x100:
        raise Exception(f"Too many metatiles definitions ({nb_metatiles}).")

    # return the metatilemap and the list of metatiles
    return metatilemap, metatiles


# serialize a list of metatiles into a .bin file
def serialize_metatiles(metatiles, path):
    with open(path, "bw+") as file:
        # serialize the metatiles
        for index in range(4 * 4 + 1):
            for metatile in metatiles:
                file.write(metatile[index])


if __name__ == "__main__":
    main()
