"""
    Serialize a sequence of bytes into ASM syntax
"""

from numpy           import ndarray
from .text_formatter import TextFormatter


# Serialize buffers of data using assembly syntax
class SerialToAsm:

    # period labels
    _LABELS_PERIOD = ['.byte', '.word', '.long', '.quad', '.octa']


    # D-labels
    _LABELS_D = ['db', 'dw', 'dd', 'dq', 'ddq']


    # GBBasic label (only supports 8-bits words)
    _LABELS_GBASIC = ['data']


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
        notation    : str  = '0x',
        uppercase   : bool = False,
        labels      : str  = 'PERIOD',
        text_format : TextFormatter = None):
        """
        Create a config for serializing buffer of data into assembly syntax
        """

        # Which set of labels to use
        if   labels == 'PERIOD' : self.labels = SerialToAsm._LABELS_PERIOD
        elif labels == 'D'      : self.labels = SerialToAsm._LABELS_D
        elif labels == 'GBASIC' : self.labels = SerialToAsm._LABELS_GBASIC
        else: raise Exception(f"Unknown label set {labels}.")

        # Select the hexadecimal notation to use
        self.format = SerialToAsm._FORMAT_HEX_UPPER if uppercase else SerialToAsm._FORMAT_HEX_LOWER

        # Select how to annotate the hexadecimal numbers
        if   notation == '0x' : self.annote = lambda s: f'0x{s}'
        elif notation == '$'  : self.annote = lambda s: f'${s}'
        elif notation == 'h'  : self.annote = lambda s: f'{s}h'
        else: raise Exception(f"Unknown hexadecimal notation {notation}.")

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
            idx = self._idx_size(matrix.dtype.itemsize)
            lbl = self.labels[idx]
            fmt = self.format[idx]
            tkn = [self.annote(fmt(n)) for n in matrix]
            return '{} {}'.format(lbl, ', '.join(tkn))

        # generate paragraphs
        else:
            sep = '\n' * (dim - 1)
            blk = [self.serialize_matrix(sub) for sub in matrix]
            return sep.join(blk)


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

        idx = self._idx_size(intsize)
        lbl = self.labels[idx]
        fmt = self.format[idx]
        tkn = [self.annote(fmt(n)) for n in array]

        # add a zero guard if requested
        if zeroguard: tkn.append('0')

        # generate assembly line
        return '{} {}'.format(lbl, ', '.join(tkn))


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

        lbl = self.labels[0]
        fmt = self.format[0]

        # generate lines to serialize
        lines = self.text_format.convert(text)

        # generate assembly lines
        output = []
        for line in lines:
            # serialize the line with a zero guard at the end
            tkn = [self.annote(fmt(n)) for n in line]
            ent = '{} {}, 0'.format(lbl, ', '.join(tkn))
            output.append(ent)

        # create a paragraph
        return '\n'.join(output)

