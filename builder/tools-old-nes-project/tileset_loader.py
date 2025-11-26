# image util
# loader for images

import numpy
from PIL import Image


# A loader for tileset and spritesheets
# Analyse the input image to determine how to generate a tileset from it
class TileSetLoader:

    # Create a new tileset loader with the given parameters
    def __init__(self, is_spritesheet=False, large_sprites=False):
        self.is_spritesheet = is_spritesheet
        self.large_sprites  = large_sprites

        # tiles can be either 8×8 or 8×16
        self.tile_shape = (8, 16 if large_sprites else 8)

        # buffer and shift matrix used to perform tile comparison
        self.shift_matrix      = numpy.full (self.tile_shape, 32, dtype=numpy.uint32)
        self.comparison_buffer = numpy.zeros(self.tile_shape,     dtype=numpy.uint64)

        # tilemap and tileset to be generated
        self.tilemap = None
        self.tileset = [ (None, None) for _ in range(0x80 if large_sprites else 0x100) ]


    # check that the input image is usable
    def __load_image(self, path):
        with Image.open(path) as image:
            matrix = numpy.asarray(image)

            # check if the matrix has valid dimensions
            if len(matrix.shape) < 2:
                raise Exception("Input data is not of a 2 dimensional array.")

            height, width, *_ = matrix.shape
            if width % self.tile_shape[0] != 0 or height % self.tile_shape[1] != 0:
                raise Exception(f"Input data is not a multiple of {self.tile_shape[0]}×{self.tile_shape[1]}.")

            # if the matrix was in RGB or RGBA format, convert it into indexed
            if len(matrix.shape) >= 3 and matrix.shape[2] >= 3:
                matrix = numpy.apply_along_axis(TileSetLoader.__combine_values, axis=2, arr=matrix)

            # split the matrix into 8 by 8 tiles
            width  //= self.tile_shape[0]
            height //= self.tile_shape[1]
            return matrix.reshape(height, self.tile_shape[1], width, self.tile_shape[0]).transpose(2, 0, 3, 1)


    # combine values into a single integer
    @staticmethod
    def __combine_values(values):
        result = 0
        for index, value in enumerate(values):
            result |= (value & 0xFF) << (index * 8)
        return result


    # load an image and convert it into a tileset
    def load_tileset(self, path):
        try:
            matrix = self.__load_image(path)
            tilemap_shape = (matrix.shape[0], matrix.shape[1])
            palettes = numpy.empty(tilemap_shape, dtype=object)
            all_palettes      = set()
            complete_palettes = set()

            # check each 8×8 (or 8×16) tile and verify it contains only 4 different colors maximum
            for tile_x, tile_y in numpy.ndindex(tilemap_shape):
                palette = TileSetLoader.extract_palette(matrix[tile_x, tile_y])

                # if the tile contains more than 4 colors, it is invalid
                nb_colors = len(palette)
                if nb_colors > 4:
                    raise Exception(f"Tile at {tile_x}×{tile_y} has more than 4 colors ({nb_colors}).")
                else:
                    # otherwise, it is a valid palette
                    all_palettes.add(palette)
                    if nb_colors == 4:
                        complete_palettes.add(palette)

                # store the colors found into the palettes matrix
                palettes[tile_x, tile_y] = palette

            # check that we do not exceed 4 palettes
            nb_palettes = len(complete_palettes)
            if nb_palettes > 4:
                raise Exception(f"Too many palettes ({nb_palettes}).")
            # assign an order to the complete palettes
            complete_palettes = list(complete_palettes)
            complete_palettes.sort()

            # prepare a tilemap and a tileset to store the results
            self.tilemap = numpy.zeros((matrix.shape[0], matrix.shape[1], 3), dtype=numpy.uint)

            # compare tiles to check if the patterns match
            for tile_x, tile_y in numpy.ndindex(tilemap_shape):
                tile1   = matrix  [tile_x, tile_y]
                palette = palettes[tile_x, tile_y]
                nb_colors1 = len(palette)

                # prepare data to store in the tilemap
                tile_data = self.tilemap[tile_x, tile_y]
                palette_index, palette = TileSetLoader.get_complete_palette(palette, complete_palettes)

                # check if a matching tile has been already added to the tileset

                # first unassigned tile in the tileset
                # such that it can be used to store the tile data if it is a new tile
                selected_tile_index = len(self.tileset)

                # if we use large sprites, we need to double the index value
                index_factor = 2 if self.large_sprites else 1

                # check each tile in the tileset
                for tile_index, (tile2, nb_colors2) in enumerate(self.tileset):
                    # tile index has not been assigned a tile yet
                    # it can be used to store the tile data if it is a new tile
                    if tile2 is None or nb_colors2 is None:
                        selected_tile_index = min(tile_index, selected_tile_index)
                        continue

                    result, flip = self.compare_tiles(tile1, nb_colors1, tile2, nb_colors2)
                    if result:
                        # if a matching tile has been found, 
                        # store the corresponding index in the tilemap
                        tile_data[0] = tile_index * index_factor
                        tile_data[1] = palette_index
                        tile_data[2] = flip
                        break
                else:
                    # if no matching tile has been found, add a new one
                    if selected_tile_index < len(self.tileset):
                        self.tileset[selected_tile_index] = (TileSetLoader.simplify_tile(tile1, palette), nb_colors1)
                        tile_data[0] = selected_tile_index * index_factor
                        tile_data[1] = palette_index
                    else:
                        raise Exception(f"Too many tiles used.")

            # return the tilemap and the associated tileset
            return self.tilemap, self.tileset

        except Exception as e:
            raise Exception(f"Error while loading {path}.") from e


    # load a fontset
    def load_fontset(self, path):
        if path is None:
            return None

        try:
            matrix = self.__load_image(path)
            tilemap_shape = (matrix.shape[0], matrix.shape[1])

            # check each 8×8 (or 8×16) tile and verify it contains only 4 different colors maximum
            for index, (tile_x, tile_y) in enumerate(numpy.ndindex(tilemap_shape)):
                tile = matrix[tile_x, tile_y]
                palette = TileSetLoader.extract_palette(tile)
                nb_colors = len(palette)

                # if the tile contains more than 4 colors, it is invalid
                if nb_colors > 4:
                    raise Exception(f"Tile at {tile_x}×{tile_y} has more than 4 colors ({nb_colors}).")

                # valid palette size, the tile represent a character
                # or empty tile and space character
                elif nb_colors >= 2 or index == 0x20:
                    self.tileset[index] = (TileSetLoader.simplify_tile(tile, palette), nb_colors)

            # return the fontset generated
            return self.tileset

        except Exception as e:
            raise Exception(f"Error while loading {path}.") from e


    # compare two tiles to check if they match
    # return a tuple containing the result and the flip direction
    def compare_tiles(self, tile1, nb_colors1, tile2, nb_colors2):
        if nb_colors1 != nb_colors2:
            return False, -1

        # check that the combined tile has a palette of the same size
        if self.__compare_tiles(tile1, tile2, nb_colors1):
            return True, 0b00

        # in case of a spritesheet, we can flip the tile in two directions
        elif self.is_spritesheet:
            flipped = numpy.fliplr(tile2)
            if self.__compare_tiles(tile1, flipped, nb_colors1):
                return True, 0b01
            elif self.__compare_tiles(tile1, numpy.flipud(tile2), nb_colors1):
                return True, 0b10
            elif self.__compare_tiles(tile1, numpy.flipud(flipped), nb_colors1):
                return True, 0b11
        return False, -1


    # compare two tiles to see if they match (modulo the colors used)
    def __compare_tiles(self, tile1, tile2, expected_color_count):
        # combine both tiles into a single matrix
        numpy.left_shift(tile2, self.shift_matrix     , out=self.comparison_buffer)
        numpy.bitwise_or(tile1, self.comparison_buffer, out=self.comparison_buffer)
        # if the amount of colors in the combined tile is not the expected amount,
        # the tiles don't match as some pixels are differents
        return len(TileSetLoader.extract_palette(self.comparison_buffer)) == expected_color_count


    # get the index and the corresponding complete palette
    @staticmethod
    def get_complete_palette(incomplete_palette, complete_palettes):
        for index, palette in enumerate(complete_palettes):
            if TileSetLoader.match_palette(incomplete_palette, palette):
                return index, palette
        return -1, []


    # check if the given incomplete palette matches the complete given palette
    @staticmethod
    def match_palette(incomplete_palette, complete_palette):
        if incomplete_palette == complete_palette:
            return True

        # check that each color in the incomplete palette is in the complete palette
        for color in incomplete_palette:
            if color not in complete_palette:
                return False

        return True


    # simplify a tile by mapping colors to values in the range [0-3]
    @staticmethod
    def simplify_tile(tile, complete_palette):
        palette = list(complete_palette)

        # map a color to a value in the range [0-3]
        map_color = lambda color: numpy.uint8(palette.index(color) if color in palette else 0)

        # return a new tile where colors are mapped to values in the range [0-3]
        return numpy.vectorize(map_color)(tile)


    # extract a palette from a tile
    @staticmethod
    def extract_palette(tile):
        palette = set()
        for x, y in numpy.ndindex(tile.shape):
            palette.add(tile[x, y])
        palette = list(palette)
        palette.sort()
        return tuple(palette)


    # convert the tileset to a .chr file
    def serialize_to_chr(self, path):

        # check that there is a tileset to write
        if self.tileset is None:
            raise Exception("No tileset to convert.")

        # write each tile in the .chr file
        with open(path, 'bw+') as file:

            # empty tile
            empty_tile = bytearray(0x20 if self.large_sprites else 0x10)

            for tile, _ in self.tileset:
                if tile is None:
                    # write an empty tile
                    file.write(empty_tile)
                else:
                    # compose the binary representation by 
                    # splitting the tile into low bits and high bits
                    low_bytes  = []
                    high_bytes = []

                    # process each row of the tile
                    for row in tile.transpose():
                        low_byte  = 0b00000000
                        high_byte = 0b00000000

                        for color_index in row:

                            # compose the low byte
                            if color_index & 0b1 != 0:
                                low_byte |= 0b1
                            low_byte <<= 1

                            # compose the high byte
                            if color_index & 0b10 != 0:
                                high_byte |= 0b1
                            high_byte <<= 1

                        low_bytes .append(low_byte)
                        high_bytes.append(high_byte)

                    # write the first 8 rows
                    file.write(bytearray(low_bytes [0:8]))
                    file.write(bytearray(high_bytes[0:8]))

                    # if the tile is a large sprite,
                    # write the 8 additional rows
                    if self.large_sprites:
                        file.write(bytearray(low_bytes [8:16]))
                        file.write(bytearray(high_bytes[8:16]))
