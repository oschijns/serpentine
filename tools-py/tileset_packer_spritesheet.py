#!/usr/bin/env python

"""
    Read Aseprite exports' to generate a packed tileset and a definition file for metasprites.
"""

import sys
import json
import numpy      as np
import imageio.v3 as iio

from os       import path
from argparse import ArgumentParser
from numpy    import ndarray

from util.tileset_system import System
from util.tileset_util   import cut_image_into_tiles, reformat_tileset, extract_tileset


def main():
    parser = ArgumentParser(
        prog="tileset_packer_spritesheet",
        description="Read Aseprite exports' to generate animated sprites for the target system.")

    parser.add_argument('-i', '--input', 
        dest='inputs',
        nargs='+',
        required=True, 
        help="A set of aseprite exports to process (.json)")

    parser.add_argument('--out-j', '--output-json',
        dest='output_json',
        required=True,
        help="Where to write the metasprite definition (.json)")

    parser.add_argument('--out-t', '--output-tileset',
        dest='output_tileset',
        required=True,
        help="Where to write the generated tileset (.png)")

    parser.add_argument('--sys', '--system',
        dest='system',
        required=True,
        choices=System.SYSTEMS,
        help="Generate a tileset compatible with the specified system")
    
    parser.add_argument('--pal', '--palette',
        dest='palette',
        required=True,
        help="Specify the order of the colors (.png)")

    args = parser.parse_args()

    # Check if the system is known
    system = System.get(args.system, True)
    if system is None:
        print(f"Unrecognized system \"{args.system}\"", file=sys.stderr)
        sys.exit(1)

    # Load the images based on the CLI
    spritesheets = []
    for input in args.inputs:
        spritesheets.append(SpriteSheet(input))

    # read provided palettes
    palettes = iio.imread(args.palette)

    # Process the provided data
    tileset = process(spritesheets, palettes, system)
    metasprites = to_serial(spritesheets, system)

    # Write the results to files
    iio.imwrite(args.output_tileset, reformat_tileset(tileset, palettes))
    json_str = json.dumps(metasprites, indent = 4)
    with open(args.output_json, 'w') as file:
        file.write(json_str)


# Define a frame
class Frame:

    # Extract data from the JSON payload
    def __init__(self, obj: dict):

        # Check that the payload is sane
        if not('frame' in obj and 'duration' in obj):
            raise Exception("Invalid frame format, 'frame' or 'duration' is missing.")

        # rectangle where the frame is stored
        rect = obj['frame']
        if not('x' in rect and 'y' in rect and 'w' in rect and 'h' in rect):
            raise Exception("Invalid frame format, 'x', 'y', 'w' or 'h' is missing.")

        self.x = int(rect['x'])
        self.y = int(rect['y'])
        self.w = int(rect['w'])
        self.h = int(rect['h'])

        # duration of the frame in milliseconds
        self.duration = int(obj['duration'])

    # Extract a sub portion of an image
    def extract(self, image: ndarray) -> ndarray:
        return image[self.y:self.y + self.h, self.x:self.x + self.w]

    # Given an indexed map, convert it into a dictionary to be serialized
    def to_serial(self,
        indexed_map   : ndarray,
        tile_size     : tuple[int, int],
        origin_offset : tuple[int, int],
        empty_tile    : int
        ) -> dict:
        """
        Convert an indexed map into a dictionary that can trivially be serialized
        into JSON.

        @type  indexed_map: ndarray (mh, mw, 3) uint16
        @param indexed_map: The pixel art converted into a tilemap with the following data:
        - tile index
        - palette index
        - flipping

        @type  tile_size: (int, int)
        @param tile_size: Size of an individual tile

        @type  origin_offset: (int, int)
        @param origin_offset: Where to place the origin of the metasprite

        @type  empty_tile: int
        @param empty_tile: Index of the empty tile

        @rtype:   dict
        @returns: Dictionary that can be trivially serialized as JSON
        """

        # Metasprites are made of multiple hardware sprites
        sprites: list[dict] = []

        # Iterate over the tiles in the map
        for iy, ix in np.ndindex(indexed_map.shape[:2]):

            # Read tile data
            tile: ndarray = indexed_map[iy, ix]
            tile_index = int(tile[0])
            palette    = int(tile[1])
            flipping   = int(tile[2])

            # If the tile is empty, move on to the next one
            if tile_index == empty_tile: continue

            # Compose a sprite
            sprites.append({
                'tile'    : tile_index,
                'palette' : palette,
                'y'       : int(iy * tile_size[0] - origin_offset[0]),
                'x'       : int(ix * tile_size[1] - origin_offset[1]),
                'flip_v'  : (flipping & 0b01) != 0,
                'flip_h'  : (flipping & 0b10) != 0,
            })

        return {
            'sprites'  : sprites,
            'duration' : self.duration,
        }



# Define a sequence of frames
class Sequence:

    # Extract data from the JSON payload
    def __init__(self, tag: dict, frames: list[dict]):

        # Check that the payload is sane
        if not ('name' in tag and 'from' in tag and 'to' in tag):
            raise Exception("Invalid frameTag format, missing 'name', 'from' or 'to'.")

        # extract relevant data
        self.name: str = tag['name']

        # parse the metadata
        if 'data' in tag:
            # list of tags to look for:
            # - "flip-h"
            # - "flip-v"
            # - "left"
            # - "right"
            # - "up"
            # - "down"
            meta: list[str] = [
                t.strip().lower().replace('-', '_')
                for t in tag['data'].split(',')
            ]

            self.flip_h = 'flip_h' in meta # flip the animation horizontally
            self.flip_v = 'flip_v' in meta # flip the animation vertically

            left  = 'left'  in meta
            right = 'right' in meta
            up    = 'up'    in meta
            down  = 'down'  in meta

            if left and right:
                raise Exception("Cannot use both 'left' and 'right' tags at the same time.")

            if up and down:
                raise Exception("Cannot use both 'up' and 'down' tags at the same time.")

            self.dir_left = left # looking toward the left?
            self.dir_down = down # looking downward?

        else:
            self.flip_h   = False
            self.flip_v   = False
            self.dir_left = False
            self.dir_down = False

        # Get the number of frame to process for this sequence
        start = int(tag['from'])
        stop  = int(tag['to']) + 1

        # store the frames in a list
        self.sequence: list[Frame] = []
        for i in range(start, stop):
            self.sequence.append(Frame(frames[i]))


    # Process the provided data and store the result in the current sequence
    def process(self,
        image      : ndarray,
        palettes   : ndarray,
        system     : System,
        tileset    : ndarray,
        used_tiles : ndarray):
        """
        Use the provided image to generate a sequence of animated metasprites

        @type  image: ndarray (ih, iw, 3) uint8
        @param image: The pixel art to extract tiles from

        @type  palettes: ndarray (pc, ps, 3) uint8
        @param palettes: Palettes provided

        @type  system: System
        @param system: Target system configuration

        @type  tileset: ndarray (tc, th, tw) uint8
        @param tileset: Tileset to store the tiles in

        @type  used_tiles: ndarray (tc) bool
        @param used_tiles: Specify if a tile has been already assigned
        """

        # make lists to store the animation frames
        flip_vh = self.flip_v and self.flip_h
        self.frames: list[ndarray] = []
        self.frames_flipped_v : list[ndarray] | None = [] if self.flip_v else None
        self.frames_flipped_h : list[ndarray] | None = [] if self.flip_h else None
        self.frames_flipped_vh: list[ndarray] | None = [] if flip_vh     else None

        # generate frames
        for element in self.sequence:
            # extract the actual frame from the spritesheet and cut it into tiles
            sub_img = element.extract(image)
            (tile_map0, pal_map0) = cut_image_into_tiles(sub_img, palettes, system.tile_size())

            # create views over the maps with the various flipping combinations
            (tile_map1, pal_map1) = (np.flip(tile_map0, (0, 2)), np.flipud(pal_map0))
            (tile_map2, pal_map2) = (np.flip(tile_map0, (1, 3)), np.fliplr(pal_map0))
            (tile_map3, pal_map3) = (np.flip(tile_map0), np.flip(pal_map0))

            # shortcut for quickly processing the tiles
            flipping = system.flipping()
            func = lambda tile_map, pal_map: extract_tileset(
                tile_map, pal_map, flipping, tileset, used_tiles)

            # identify tiles with all flipping configurations
            self.frames.append(func(tile_map0, pal_map0))
            if self.flip_v: self.frames_flipped_v .append(func(tile_map1, pal_map1))
            if self.flip_h: self.frames_flipped_h .append(func(tile_map2, pal_map2))
            if flip_vh    : self.frames_flipped_vh.append(func(tile_map3, pal_map3))


    # Convert the sequence into a dictionary to be serialized
    def to_serial(self,
        tile_size     : tuple[int, int],
        origin_offset : tuple[int, int],
        empty_tile    : int
        ) -> list[dict] | dict[str, list[dict]]:
        """
        Convert the sequence into a dictionary that can trivially be serialized
        into JSON.

        @type  tile_size: (int, int)
        @param tile_size: Size of an individual tile

        @type  origin_offset: (int, int)
        @param origin_offset: Where to place the origin of the metasprite

        @type  empty_tile: int
        @param empty_tile: Index of the empty tile

        @rtype:   one or multiple list( dict )
        @returns: Structure that can be trivially serialized as JSON
        """

        # Convert a sequence of frames
        def func(frames: list[ndarray] | None) -> list[dict] | None:
            if frames is not None:
                metasprites: list[dict] = []
                for frame_def, frame_data in zip(self.sequence, frames):
                    metasprites.append(frame_def.to_serial(frame_data, tile_size, origin_offset, empty_tile))
                return metasprites
            else:
                return None

        # process the frames
        frames    = func(self.frames)
        frames_v  = func(self.frames_flipped_v)
        frames_h  = func(self.frames_flipped_h)
        frames_vh = func(self.frames_flipped_vh)

        # flip both vertically and horizontally
        if self.flip_v and self.flip_h:
            up_right  : list[dict] = frames
            up_left   : list[dict] = frames_h
            down_right: list[dict] = frames_v
            down_left : list[dict] = frames_vh

            # swap metasprites vertically
            if self.dir_down:
                (up_right, down_right) = (down_right, up_right)
                (up_left , down_left ) = (down_left , up_left )

            # swap metasprites horizontally
            if self.dir_left:
                (up_right  , up_left  ) = (up_left  , up_right  )
                (down_right, down_left) = (down_left, down_right)

            return {
                'down_left' : down_left,
                'down_right': down_right,
                'up_left'   : up_left,
                'up_right'  : up_right,
            }

        # flip only vertically
        elif self.flip_v:
            (down, up) = (frames, frames_v) if self.dir_down else (frames_v, frames)
            return {'down': down, 'up': up}

        # flip only horizontally
        elif self.flip_h:
            (left, right) = (frames, frames_h) if self.dir_left else (frames_h, frames)
            return {'left': left, 'right': right}

        # no flipping
        else:
            return frames


# Define a spritesheet for an animated object
class SpriteSheet:

    # Load a JSON file generated by aseprite
    def __init__(self, file_path: str):
        # Read the JSON file
        with open(file_path, 'r') as file:
            self.json = json.load(file)

        # Check provided file is valid
        if self.json is None:
            raise Exception(f"Provided file is empty \"{file_path}\"")
        elif 'frames' not in self.json or type(self.json['frames']) is not list:
            raise Exception(f"Missing entry 'frames' of type 'list' in JSON file \"{file_path}\"")
        elif 'meta' not in self.json:
            raise Exception(f"Missing entry 'meta' in JSON file \"{file_path}\"")

        meta  : dict       = self.json['meta'  ]
        frames: list[dict] = self.json['frames']

        if 'image' not in meta:
            raise Exception(f"Missing entry 'meta.image' in JSON file \"{file_path}\"")
        elif 'frameTags' not in meta:
            raise Exception(f"Missing entry 'meta.frameTags' in JSON file \"{file_path}\"")

        # Get the name of the image to load, 
        # should be placed next to the currently loaded JSON file
        im_name: str = meta['image']
        im_path: str = path.join(path.dirname(file_path), im_name)

        # Get the name of the spritesheet
        self.name = im_name.split('.', 1)[0]

        # Load the image
        self.image = iio.imread(im_path)

        # Get the frame tags
        frame_tags: list[dict] = meta['frameTags']
        self.sequences: list[Sequence] = []
        for tag in frame_tags:
            self.sequences.append(Sequence(tag, frames))

        # Where to place the origin of the metasprite
        self.origin_offset = (0, 0)


    # Process the image that was loaded
    def process(self, 
        palettes   : ndarray, 
        system     : System,
        tileset    : ndarray,
        used_tiles : ndarray):
        """
        Use the provided images to generate a tileset

        @type  palettes: ndarray (pc, ps, 3) uint8
        @param palettes: Palettes provided

        @type  system: System
        @param system: Target system configuration

        @type  tileset: ndarray (tc, th, tw) uint8
        @param tileset: Tileset to store the tiles in

        @type  used_tiles: ndarray (tc) bool
        @param used_tiles: Specify if a tile has been already assigned
        """

        # Generate frames for each sequence and populate the tileset
        for sequence in self.sequences:
            sequence.process(self.image, palettes, system, tileset, used_tiles)


    # Process the image that was loaded
    def to_serial(self, system: System) -> dict:
        """
        Serialize the spritesheet into a JSON format

        @type  system: System
        @param system: Target system configuration

        @rtype:   dict
        @returns: Structure that can be trivialily serialized to JSON
        """

        # Compose metasprites
        metasprites = {}
        tile_size   = system.tile_size()
        empty_tile  = system.tile_count

        # Generate frames for each sequence and populate the tileset
        for sequence in self.sequences:
            metasprites[sequence.name] = sequence.to_serial(
                tile_size, self.origin_offset, empty_tile)

        return metasprites


# Process the data
def process(
    spritesheets : list[SpriteSheet], 
    palettes     : ndarray, 
    system       : System,
    ) -> ndarray:
    """
    Use the provided spritesheets to generate a tileset

    @type  spritesheets: list( SpriteSheet )
    @param spritesheets: The pixel art to extract tiles from

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

    # Allocate a buffer to store the generated tileset
    # Add an extra trailing tileset to handle empty tiles
    empty_tile =  system.tile_count
    shape      = (system.tile_count + 1, system.tile_height, system.tile_width)
    tileset    = np.zeros(shape   , np.uint8)
    used_tiles = np.zeros(shape[0], np.bool )
    used_tiles[empty_tile] = True

    # Process the spritesheets
    for spritesheet in spritesheets:
        spritesheet.process(palettes, system, tileset, used_tiles)

    # remove the extra tile
    return tileset[:-1]


# Build a JSON structure for the spritesheet
def to_serial(
    spritesheets : list[SpriteSheet],
    system       : System,
    ) -> dict[str, dict]:
    """
    Use the provided spritesheets to generate a tileset

    @type  spritesheets: list( SpriteSheet )
    @param spritesheets: The pixel art to extract tiles from

    @type  system: System
    @param system: Target system configuration

    @rtype: dict( str -> dict )
    @returns: Structure to be serialized as JSON
    """

    # Process the spritesheets
    data: dict[str, dict] = {}
    for spritesheet in spritesheets:
        data[spritesheet.name] = spritesheet.to_serial(system)

    return data


if __name__ == '__main__':
    main()