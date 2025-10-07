"""
    Convert ASCII text into another arbitrary encoding
"""

import numpy as np

from numba import njit, prange
from numpy import ndarray


# Configuration for character remapping
class TextFormatter:

    
    def __init__(self, remap_char : dict[str, int]):
        # TODO: process remap array
        self.remap = np.zeros(256, dtype=np.uint8)


# Remap characters
@njit(fastmath=True)
def remap_characters(text: ndarray, remap: ndarray) -> ndarray:
    """
    Read the provided text using ASCII encoding and remap the characters into the target encoding.

    @type  text: ndarray (n) uint8
    @param text: The input text encoded in ASCII

    @type  remap: ndarray (r) uint8
    @param remap: Remapping rules, for each ASCII character, specify the byte to replace it with

    @rtype:   ndarray (n) uint8
    @returns: The output text
    """

    # remap struct should have an entry for each ASCII character
    if remap.shape[0] >= 256:
        raise Exception("Invalid remap array")

    # allocate a buffer to store the result
    size   = text.shape[0]
    output = np.zeros(size, dtype=np.uint8)

    # convert the characters
    for i in prange(size):
        output[i] = remap[text[i]]
    
    return output