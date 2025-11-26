#!/usr/bin/python3

import numpy
from argparse import ArgumentParser
from tileset_loader import TileSetLoader
from generator_util import generate_wiz


# load a image to constitute a spritesheet
# the first image define the metasprites
# the second image define the alphabet (optional)
# generate a .chr file containing the spritesheet
# generate a .wiz file containing the metasprites definitions
def main():
    parser = ArgumentParser(prog="make_sprites")

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

    # output metasprites generated
    parser.add_argument("-m", "--metasprites",
                        dest="metasprites",
                        required=True,
                        metavar="FILE",
                        help="output .wiz file")

    # read the command line arguments
    args = parser.parse_args()

    # load an image to constitute a tileset
    loader = TileSetLoader()
    loader.load_fontset(args.font)
    tilemap, _ = loader.load_tileset(args.image)

    # group up joined sprites into metasprites
    metasprites = compose_metasprites(tilemap)

    # write the tileset file
    loader.serialize_to_chr(args.tileset)

    # write the metasprites file
    generate_wiz(metasprites, args.metasprites, variable="sprite",
        namespace="metasprites", comment="Generated sources")


# group up joined sprites into metasprites
def compose_metasprites(tilemap, empty_tile=0):
    islands = get_islands_indexes(tilemap, empty_tile)

    # sequences of metasprites to compose
    sequences = []
    for island in islands:
        # sequence of bytes
        sequence = numpy.zeros(len(island) * 4, dtype=numpy.uint8)

        # get the starting position of the island
        start_x = min(island, key = lambda x: x[0])[0]
        start_y = min(island, key = lambda x: x[1])[1]
        for index, (x, y) in enumerate(island):
            tile_data = tilemap[x, y, :]

            # write data in the sequence
            offset = index * 4
            sequence[offset + 0] = y - start_y
            sequence[offset + 1] = tile_data[0]
            sequence[offset + 2] = (tile_data[2] << 6) | tile_data[1]
            sequence[offset + 3] = x - start_x

        sequences.append(sequence)

    return sequences


# group up joined sprites into islands
def get_islands_indexes(tilemap, empty_tile=0):

    # compose islands using Depth-First Search (DFS) algorithm

    # create a list to store the islands
    islands = []
    width, height, _ = tilemap.shape
    visited = numpy.zeros((width, height), dtype=bool)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    # DFS algorithm
    def depth_first_search(x0, y0):
        island = []
        stack = [(x0, y0)]

        # repeat until the stack is empty
        while stack:
            x, y = stack.pop()
            if visited[x, y]:
                continue
            visited[x, y] = True
            island.append((x, y))

            # check neighboring cells
            for dx, dy in directions:
                new_x = x + dx
                new_y = y + dy
                if not visited[new_x, new_y] and tilemap[new_x, new_y, 0] != empty_tile:
                    stack.append((new_x, new_y))

        island.sort()
        return island

    # iterate through the tilemap
    for x, y in numpy.ndindex(tilemap.shape):
        if not visited[x, y] and tilemap[x, y, 0] != empty_tile:
            islands.append(depth_first_search(x, y))

    return islands


if __name__ == "__main__":
    main()
