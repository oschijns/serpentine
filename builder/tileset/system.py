"""
    Define retro systems' configurations
"""

import math

from numpy  import ndarray
from typing import Self

# Define a system tile configuration
class System:

    # Store a list of systems
    SYSTEMS = []

    # Store configurations for sprites
    CONFIG_SPRITES = {}

    # Store configurations for tilemaps
    CONFIG_TILEMAPS = {}

    # Create a config from a set of parameters
    def __init__(self, 
        name          : str,
        is_sprite     : bool = False,
        pal_count     : int  = 4, 
        pal_size      : int  = 4,
        tile_count    : int  = 256,
        intertwined   : int  = 2,
        flip_h        : bool = True,
        flip_v        : bool = True,
        use_bitplanes : bool = True,
        tile_width    : int  = 8,
        tile_height   : int  = 8):

        self.name = name

        # check_palette
        self.palette_count = pal_count
        self.palette_size  = pal_size

        # cut_image_into_tiles, reshape_tileset
        self.tile_count  = tile_count
        self.tile_width  = tile_width
        self.tile_height = tile_height

        # tile_packer
        self.flipping_h = flip_h
        self.flipping_v = flip_v

        # bitplane
        self.intertwined   = intertwined
        self.bit_count     = int(math.log2(pal_size))
        self.use_bitplanes = use_bitplanes

        # Store the element in the appropriate list
        if is_sprite:
            Self.CONFIG_SPRITES[self.name] = self
        else:
            Self.CONFIG_TILEMAPS[self.name] = self
        
        # Specify that the system exists
        if self.name not in Self.SYSTEMS:
            Self.SYSTEMS.append(self.name) 


    # Print a string representation of the system
    def __repr__(self):
        return f"""{self.name}:
    tile:
        count:  {self.tile_count}
        width:  {self.tile_width}
        height: {self.tile_height}
    palette:
        count: {self.palette_count}
        size:  {self.palette_size}
    flipping:
        horizontal: {'true' if self.flipping_h else 'false'}
        vertical:   {'true' if self.flipping_v else 'false'}
"""

    # Check if the given palette is valid for this system
    def check_palette(self, palette: ndarray) -> bool:
        pal_count = palette.shape[0]
        pal_size  = palette.shape[1]
        return (self.palette_count == pal_count and 
                self.palette_size  == pal_size)

    # Get the size of a tile
    def tile_size(self) -> tuple[int, int]:
        return (self.tile_height, self.tile_width)

    # Get a tuple to allocate a tileset buffer
    def tileset_shape(self) -> tuple[int, int, int]:
        return (self.tile_count, self.tile_height, self.tile_width)
    
    # Get flipping possibilities for this system
    def flipping(self) -> tuple[bool, bool]:
        return (self.flipping_v, self.flipping_h)
    
    # Get the size of the serialize tileset in bytes
    def serial_size(self) -> int:
        return self.tile_count * self.bit_count * 8


    # Load system configs
    @staticmethod
    def get(name: str, is_sprite: bool = False) -> Self | None:
        if is_sprite:
            return Self.CONFIG_SPRITES.get(name)
        else:
            return Self.CONFIG_TILEMAPS.get(name)


# Nintendo Entertainment System
System('nes',
    flip_h    = False, 
    flip_v    = False)
System('nes', 
    is_sprite = True)

# Super Nintendo Entertainment System
System('snes',
    pal_count  =   16,
    pal_size   =   16,
    tile_count = 1024)
System('snes',
    is_sprite  = True,
    pal_count  =   16,
    pal_size   =   16,
    tile_count = 1024)

# Nintendo GameBoy
System('gb',
    pal_count = 1,
    flip_h    = False,
    flip_v    = False)
System('gb',
    is_sprite = True,
    pal_count = 1,
    flip_h    = False,
    flip_v    = False)

# Nintendo GameBoy Color
System('gbc',
    pal_count = 8)
System('gbc',
    is_sprite = True,
    pal_count = 8)

# Sega Master System
System('sms',
    pal_count   =  2,
    pal_size    = 16,
    intertwined =  4)

System('sms',
    is_sprite   = True,
    pal_count   =  2,
    pal_size    = 16,
    intertwined =  4,
    flip_h      = False,
    flip_v      = False)

# Sega Megadrive
System('md',
    pal_count   =    4,
    pal_size    =   16,
    intertwined =    4,
    tile_count  = 2048)

System('md',
    is_sprite   = True,
    pal_count   =    4,
    pal_size    =   16,
    intertwined =    4,
    tile_count  = 2048)

# NEC PC-Engine
#System('pce',
#    pal_count = 16, # ?
#    pal_size  = 16, # ?
#    )

# SNK NeoGeo Pocket Color
#System('ngpc',
#    pal_count = 4, # ?
#    pal_size  = 4, # ?
#    )

# Bandai Wonderswan Color
#System('wsc',
#    pal_count   = 4, # ?
#    pal_size    = 4, # ?
#    intertwined = 4,
#    )