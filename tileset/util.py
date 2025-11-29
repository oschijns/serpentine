"""
    Common tools to process tileset data.
"""

import numpy as np
from numba import njit, prange
from numpy import ndarray


# Reshape the image into a matrix of tiles
@njit(fastmath=True)
def cut_image_into_tiles(
    image     : ndarray,
    palettes  : ndarray,
    tile_size : tuple[int, int],
    origin    : tuple[int, int] = (0, 0)
    ) -> tuple[ndarray, ndarray]:
    """
    Reshape the image into a matrix of tiles of size width x height.

    @type  image: ndarray (ih, iw, 3) uint8
    @param image: The input pixel art to process

    @type  palettes: ndarray (pc, ps, 3) uint8
    @param palettes: The palettes for conversion from RGB to index

    @type  tile_size: (int, int)
    @param tile_size: Height and width of a tile

    @type  origin: (int, int)
    @param origin: Origin of the image (for debugging)

    @rtype:   (ndarray (mh, mw, th, tw) uint8, ndarray (mh, mw) uint8)
    @returns: The image split into tiles with indexed pixels and a map of palette indexes
    """

    # Prepare the output buffer
    tile_h : int = tile_size[0]
    tile_w : int = tile_size[1]
    out_h  : int = image.shape[0] // tile_h
    out_w  : int = image.shape[1] // tile_w
    output : ndarray = np.zeros((out_h, out_w, tile_h, tile_w), np.uint8)
    pal_map: ndarray = np.zeros((out_h, out_w), np.uint8)

    # Copy each RGB pixel from the input image to its new location
    for iy in prange(out_h):
        for ix in prange(out_w):
            # Extract an RGB tile from the input image
            y0: int = iy * tile_h ; y1: int = y0 + tile_h
            x0: int = ix * tile_w ; x1: int = x0 + tile_w

            # Convert it into an indexed tile
            tile_pos: tuple[int, int, int, int] = (origin[0], origin[1], + ix, iy)
            (tile, pal_index) = identify_palette(image[y0:y1, x0:x1], palettes, tile_pos)
            output [iy, ix] = tile
            pal_map[iy, ix] = pal_index

    # return the image cut into tiles with palette map
    return (output, pal_map)



# Given a matrix of tiles, reshape it into a simple sequence
@njit(fastmath=True)
def reshape_tileset(
    tilemap   : ndarray,
    set_shape : tuple[int, int, int],
) -> ndarray:
    """
    Reshape the tilemap into a tileset

    @type  tilemap: ndarray (mh, mw, th, tw) uint8
    @param tilemap: The tilemap to reshape

    @type  set_shape: (int, int, int)
    @param set_shape: Specify the shape of the tileset

    @rtype: ndarray (tc, th, tw) uint8
    @returns: The reshaped tileset
    """
    row_length: int = tilemap.shape[1]

    # Allocate a buffer to store the generated tileset
    tileset = np.zeros(set_shape, np.uint8)
    for iy, ix in np.ndindex(tilemap.shape[:2]):
        tileset[ix + iy * row_length] = tilemap[iy, ix]

    # Return the tileset as a sequence
    return tileset



# Given a tile which pixels are encoded as RGB values and a palette, try to 
# identify a matching palette to use. If one is found, return the tile where each
# pixel is identified as an index.
@njit(fastmath=True)
def identify_palette(
    tile     : ndarray, 
    palettes : ndarray, 
    tile_pos : tuple[int, int, int, int],
) -> tuple[ndarray, int]:
    """
    Try to find a palette that matches with the tile

    @type  tile: ndarray (th, tw, 3) uint8
    @param tile: The RGB tile to convert

    @type  palettes: ndarray (pc, ps, 3) uint8
    @param palettes: The palette convert pixels from RGB to index

    @type  tile_pos: tuple[int, int, int, int]
    @param tile_pos: Position of the tile in the image (for debugging)

    @rtype:   (ndarray (th, tw) uint8, int)
    @returns: The tile with indexes and the index of the palette identified
    """

    # Prepare a storage area to find the best matching palette
    pal_count: int = palettes.shape[0]
    pal_size : int = palettes.shape[1]
    tile_h   : int = tile    .shape[0]
    tile_w   : int = tile    .shape[1]
    storage: ndarray = np.full((pal_count, tile_h, tile_w), -1, np.int8)

    # For each palette defined
    for pi in prange(pal_count):
        pal: ndarray = palettes[pi]

        # For each pixel in the tile
        for ty in prange(tile_h):
            for tx in prange(tile_w):
                pix: ndarray = tile[ty, tx]

                # Check if the pixel color is part of the palette
                # And if it is the case, store the index of the color
                for ci in prange(pal_size):
                    color: ndarray = pal[ci]
                    if cmp_rgb(pix, color):
                        storage[pi, ty, tx] = ci

    # Now each storage cell should contains a tile definition where the pixel 
    # are identified using indexes. However only one may have no negative indexes.
    for idx in range(pal_count):
        tile_def: int = storage[idx]
        if np.all(tile_def != -1):
            return (tile_def, idx)

    # Could not identify a palette for this tile
    raise Exception("Could not identify a palette for the tile.", tile_pos)



# Compare two RGB colors with an optional epsilon
@njit(fastmath=True)
def cmp_rgb(a: ndarray, b: ndarray, ep: int = 0) -> bool:
    for i in range(3):
        if abs(int(a[i]) - int(b[i])) > ep:
            return False
    return True



# Reformat the tileset into an image with multiple variations
@njit(fastmath=True)
def reformat_tileset(
    tileset       : ndarray, 
    palettes      : ndarray, 
    row_length    : int  = 16,
    pal_variation : bool = False
    ) -> ndarray:
    """
    Convert the tileset into an image format

    @type  tileset: ndarray (tc, th, tw) uint8
    @param tileset: The tileset to convert into an image

    @type  palettes: ndarray (pc, ps, 3) uint8
    @param palettes: The palettes to use to generate the variations

    @type  row_length: int (default: 8)
    @param row_length: How many tiles per rows

    @type  pal_variation: bool
    @param pal_variation: Specify if palette variations should be created

    @rtype:   ndarray (ih, iw, 3) uint8
    @returns: Reformat the tileset so that it can be written to an image file
    """

    # Get layout
    pal_count : int = palettes.shape[0] if pal_variation else 1
    tile_count: int = tileset .shape[0]
    tile_h    : int = tileset .shape[1]
    tile_w    : int = tileset .shape[2]

    # Allocate a buffer to write the image
    im_h: int = tile_h * (tile_count // row_length) * pal_count
    im_w: int = tile_w * row_length
    image: ndarray = np.zeros((im_h, im_w, 3), np.uint8)

    # Allocate a buffer to store a RGB tile
    buffer: ndarray = np.zeros((tile_h, tile_w, 3), np.uint8)
    pal_offset: int = im_h // pal_count

    # For each palette defined
    for ip in prange(pal_count):

        # For each tile in the tileset
        for it in prange(tile_count):

            # Convert each of its index back into a RGB value
            for ty in prange(tile_h):
                for tx in prange(tile_w):
                    color_index: int = tileset[it, ty, tx]
                    buffer[ty, tx] = palettes[ip, color_index]

            # Write it at the right location in the image
            iy: int = (it // row_length) * tile_h + ip * pal_offset
            ix: int = (it %  row_length) * tile_w
            image[iy : iy + tile_h, ix : ix + tile_w] = buffer

    # Return the tileset as an image
    return image



# Given a pixel art and a palette, populate a tileset and identify the palette 
# of each tile. Also for each tile replace the pixels RGB value by the 
# corresponding index of the color in the palette selected.
@njit(fastmath=True)
def extract_tileset(
    tile_map   : ndarray,
    pal_map    : ndarray,
    flipping   : tuple[bool, bool],
    tileset    : ndarray,
    used_tiles : ndarray,
    ) -> ndarray:
    """
    Given a pixel art and a palette, populate a tileset and identify the 
    palette of each tile. Also for each tile replace the pixels RGB value 
    by the corresponding index of the color in the palette selected.

    @type  tile_map: ndarray (mh, mw, th, tw, 3) uint8
    @param tile_map: The input pixel art to process

    @type  pal_map: ndarray (mh, mw) uint8
    @param pal_map: Map of palette indexes

    @type  flip_h: (bool, bool)
    @param flip_h: Allow flipping tiles horizontally and/or verticaly

    @type  tileset: ndarray (tc, th, tw) uint8
    @param tileset: Tileset to store the tiles in

    @type  used_tiles: ndarray (tc) bool
    @param used_tiles: Specify if a tile has been already assigned

    @rtype:   ndarray (mh, mw, 3) uint16
    @returns: The pixel art converted into a tilemap with the following data:
    - tile index
    - palette index
    - flipping

    The `tileset` and `used_tiles` are parameters to populate but they may contain initial values.
    """

    # Get the size of the image to iterate on
    map_h: int = tile_map.shape[0]
    map_w: int = tile_map.shape[1]

    # Get the size of the tileset (number of individual tiles)
    size: int = used_tiles.shape[0]

    # Get flipping options
    flip_v: bool = flipping[0]
    flip_h: bool = flipping[1]

    # Allocate 16 bits to account for systems which support more than 256 tiles
    output: ndarray = np.zeros((map_h, map_w, 3), np.uint16)

    # Allocate a buffer to check if a given tile matches with one in the tileset
    # - (-1) : no match
    # -   0  : match without flipping
    # -   1  : match with vertical   flipping
    # -   2  : match with horizontal flipping
    # -   3  : match with both       flipping
    buffer: ndarray = np.full(size, -1, np.int8)

    # Iterate over each tile in the image
    for iy in prange(map_h):
        for ix in prange(map_w):
            tile: ndarray = tile_map[iy, ix]

            # Check if the tile is already in the tileset
            for it in prange(size):

                # Reset the buffer to reuse it
                buffer[it] = -1

                # Test each tile that already exists in the tileset
                if used_tiles[it]:

                    # prepare the reference tile with all flipping combinations
                    tile0: ndarray = tileset[it]
                    tile1: ndarray = np.flipud(tile0)
                    tile2: ndarray = np.fliplr(tile0)
                    tile3: ndarray = np.flip  (tile0)

                    # Given initial parameters, try to find a match
                    if np.array_equal(tile, tile0):
                        buffer[it] = 0b00
                    elif flip_v and np.array_equal(tile, tile1):
                        buffer[it] = 0b01
                    elif flip_h and np.array_equal(tile, tile2):
                        buffer[it] = 0b10
                    elif flip_v and flip_h and np.array_equal(tile, tile3):
                        buffer[it] = 0b11

            # get values to store in the output map
            tile_index: int = -1
            flipping  : int = -1

            # One (or more) of the tiles match
            if np.any(buffer != -1):
                for it in range(size):
                    has_match: int = buffer[it]
                    if has_match != -1:
                        tile_index = it
                        flipping   = has_match
                        break

            # If the tile is new try to find a location where to store it
            else:
                for it in range(size):
                    if not used_tiles[it]:
                        tile_index = it
                        flipping   = 0

                        # Store the new tile and mark the location as used
                        tileset   [it] = tile
                        used_tiles[it] = True
                        break
            
            # store the tuple in the output
            output[iy, ix] = np.array([tile_index, pal_map[iy, ix], flipping])

    # return the output
    return output