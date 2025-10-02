"""
    Serialize a sequence of bytes for either C or ASM
"""

from numba import njit, prange
from numpy import ndarray


# Specify how many elements to write per line for 1D arrays
LINE_SIZE = 16


# Serialize to assembly sources
@njit
def serial_to_asm(buffer: ndarray, zeroguard: bool = False) -> str:
    # read the provided array to figure out how to serialize it
    s = buffer.dtype.itemsize
    if   s == 1:
        head = '.byte'
        fmt  = lambda n: f'${n:02x}'
    elif s == 2:
        head = '.word'
        fmt  = lambda n: f'${n:04x}'
    else:
        raise Exception(f"Unsupported type {buffer.dtype.name}.")

    # compose blocks of numbers
    s = len(buffer.shape)
    block = []

    # serialize the 1D array as lines of 16 elements
    if   s == 1:
        line = []
        for i in prange(buffer.shape[0]):
            if i > 0 and i % LINE_SIZE == 0:
                line = ','.join(line)
                block.append(f'\t{head}\t{line}')
                line = []
            line.append(fmt(buffer[i]))
        # write the last line
        if buffer.shape[0] % LINE_SIZE != 0:
            line = ','.join(line)
            block.append(f'\t{head}\t{line}')

    # serialize as a 2D array
    elif s == 2:
        for y in prange(buffer.shape[1]):
            line = []
            for x in prange(buffer.shape[0]):
                line.append(fmt(buffer[x, y]))
            line = ','.join(line)
            block.append(f'\t{head}\t{line}')

    # don't handle 3D or more arrays
    else:
        raise Exception(f"Unsupported array shape {buffer.shape}.")

    # join the lines into a block
    output = '\n'.join(block)
    return f'{output}\n\t{head}\t0' if zeroguard else output



# Serialize to C sources
@njit
def serial_to_c(buffer: ndarray, zeroguard: bool = False) -> str:
    pass