"""
    Serialize a sequence of bytes for common programming languages
"""

from numpy           import ndarray
from .text_formatter import TextFormatter


# Serialize buffers of data using assembly syntax
class SerialToLang:

    # format integer into lower case hexadecimal string
    _FORMAT_HEX_LOWER = [
        lambda n: format(int(n), '02x' ),
        lambda n: format(int(n), '04x' ),
        lambda n: format(int(n), '08x' ),
        lambda n: format(int(n), '016x'),
        lambda n: format(int(n), '032x'),
    ]


    # format integer into upper case hexadecimal string
    _FORMAT_HEX_UPPER = [
        lambda n: format(int(n), '02X' ),
        lambda n: format(int(n), '04X' ),
        lambda n: format(int(n), '08X' ),
        lambda n: format(int(n), '016X'),
        lambda n: format(int(n), '032X'),
    ]


    # Create a config for serializing buffer of data into assembly syntax
    def __init__(self, 
        uppercase   : bool = False,
        braces      : str  = '{}',
        text_format : TextFormatter = None):

        # Select the hexadecimal notation to use
        self.format = SerialToLang._FORMAT_HEX_UPPER if uppercase else SerialToLang._FORMAT_HEX_LOWER

        # Which set of labels to use
        if   braces == '{}': self.braces = '{{ {} }}'
        elif braces == '[]': self.braces = '[ {} ]'
        else: raise Exception(f"Unknown label set {braces}.")

        # If provided store a text formatter
        self.text_format = text_format


    # Get the index corresponding to the size of the provided integer type
    @staticmethod
    def _idx_size(size: int) -> int:
        if   size ==  1: return 0
        elif size ==  2: return 1
        elif size ==  4: return 2
        elif size ==  8: return 3
        elif size == 16: return 4
        else: raise Exception(f"Unsupported integer size {size}.")


    # Serialize a matrix
    def serialize_matrix(self, matrix: ndarray) -> str:
        """
        Serialize a matrix of N-dimensions to assembly syntax.

        @type  matrix: ndarray
        @param matrix: A matrix of N-dimension storing unsigned integers

        @rtype: str
        @returns: Assembly syntax that can be embedded using Jinja2
        """

        # Get the number of dimensions in the matrix
        # We have three cases to handle: 1, 2 or N
        dim = len(matrix.shape)

        # cannot handle matrix without any dimensions
        if dim <= 0:
            raise Exception("Cannot operate on matrix of null dimension")

        # generate a single line
        elif dim == 1:
            fmt = self.format[self._idx_size(matrix.dtype.itemsize)]
            tkn = [f'0x{fmt(n)}' for n in matrix]
            return self.braces.format(', '.join(tkn))

        # generate paragraphs
        else:
            tkn = [self.serialize_matrix(matrix[i]) for i in range(matrix.shape[0])]
            return self.braces.format(',\n'.join(tkn))


    # Serialize list of arbitrary size
    def serialize_list(self, 
        array     : list[int], 
        intsize   : int  = 1, 
        zeroguard : bool = False
    ) -> str:
        """
        Serialize a list

        @type  array: list
        @param array: A list of elements

        @type  intsize: int
        @param intsize: Size of the integer to serialize in bytes 

        @type  zeroguard: bool
        @param zeroguard: Specify if the list should be null terminated

        @rtype: str
        @returns: Assembly syntax that can be embedded using Jinja2
        """

        fmt = self.format[self._idx_size(intsize)]

        # generate lines to serialize
        tkn = [f'0x{fmt(n)}' for n in array]

        # add a zero guard if requested
        if zeroguard: tkn.append('0')

        # create a paragraph
        return self.braces.format(', '.join(tkn))


    # Serialize a string
    def serialize_string(self, text: str) -> str:
        """
        Serialize a string of text

        @type  text: str
        @param text: The text to serialize

        @type  intsize: int
        @param intsize: Size of the integer to serialize in bytes 

        @type  zeroguard: bool
        @param zeroguard: Specify if the list should be null terminated

        @rtype: str
        @returns: Assembly syntax that can be embedded using Jinja2
        """

        if self.text_format is None:
            raise Exception("No text formatter defined for this assembly serializer")

        fmt = self.format[0]

        # generate lines to serialize
        lines = self.text_format.convert(text)

        # generate assembly lines
        output = []
        for line in lines:
            # serialize the line with a zero guard at the end
            tkn = [self.annote(fmt(n)) for n in line]
            tkn.append('0')
            ent = self.braces.format(', '.join(tkn))
            output.append(ent)

        # create a paragraph
        return self.braces.format(',\n'.join(output))

