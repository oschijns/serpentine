"""
    Convert ASCII text into another arbitrary encoding
"""

import numpy as np
from numba import njit, prange
from numpy import ndarray


# Configuration for character remapping
class TextFormatter:

    # Create a formatter for text
    def __init__(self,
        remap_char: dict[str, int],
        max_length: int = 32):
        """
        Read the provided map and deduce a mapping ASCII to target encoding.
        The keys are a sequence of ASCII characters and the value is a start index for the sequence.

        @type  remap_char: dict[str, int]
        @param remap_char: Map a sequence of ASCII characters to a starting index

        @type  max_length: int (default 32)
        @param max_length: Maximum length of the line of text before forcing a line return
        """

        # allocate a buffer to store the mapping
        self.remap = np.zeros(256, dtype=np.uint8)

        # allow to check for already encountered characters,
        # thus raising an error if it occurs
        flags = np.zeros(256, dtype=np.bool_)

        # iterate over the map
        for seq, start in remap_char.items():
            for i, char in enumerate(seq.encode()):

                # check if the character has already been encountered
                if flags[char]:
                    raise Exception(f"Character {chr(char)} is already used")
                flags[char] = True

                # map the ASCII character to a target index
                self.remap[char] = start + i

        self.max_length = max_length


    # Convert the text into the target encoding
    def convert(self, text: str) -> list[bytes]:
        output = []

        # Split the text into lines at explicit line returns
        # and also when the line is too long.
        for line in text.splitlines():
            bline = line.encode()
            for i in range(0, len(bline), self.max_length):

                # cut the line and convert it into a numpy array
                # remap the characters into the target encoding
                # and add the line to the list
                buffer = np.frombuffer(bline[i:i+self.max_length], dtype=np.uint8)
                result = _remap_characters(buffer, self.remap)
                output.append(result.tobytes())

        return output



# Remap characters
@njit(fastmath=True)
def _remap_characters(text: ndarray, remap: ndarray) -> ndarray:
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