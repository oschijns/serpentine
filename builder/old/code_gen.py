#!/usr/bin/env python

import io
import textwrap
import numpy


# File where to write the data provided
class TargetFile:

    # Target source is C
    __TYPE_C__ = "C"

    # Target source is assembly
    __TYPE_ASM__ = "asm"

    # Constructor
    def __init__(self, file_path, type):

        # Determine the type of source to generate
        self.c_source = type == self.__TYPE_C__

        # Open the file to write to
        self.file = io.open(file_path, "w", encoding="utf-8")

    # Destructor
    def __del__(self):
        self.file.close()

    # Write a comment
    def write_comment(self, comment):
        # prepare the comment to be written
        if self.c_source:
            prefix = "//"
        else:
            prefix = ";"
        com = textwrap.indent(textwrap.dedent(comment), prefix=prefix)
        self.file.write(com)

    # Write an array of data
    def write_array(
        self, var_name, data, values_per_row=16, append_guard=False, size_var_name=None
    ):
        # reorganize the data so that it can be written to file in a ledgible form
        array = data.flatten()
        height = int(numpy.ceil(array.size / values_per_row))

        # how many elements are in the last row
        last_row_size = array.size - (height - 1) * values_per_row

        # pad the array if necessary
        if last_row_size < values_per_row:
            array = numpy.pad(array, (0, values_per_row - last_row_size))
        reshape = array.reshape(height, values_per_row)

        if self.c_source:
            # declare the array of bytes in the form
            # ```
            # const unsigned char var_name[] = {
            #     0x00, 0x00, ...
            # };
            # ```
            self.file.write(f"const unsigned char {var_name}[] = {{\n\t")

            # write each line as is except the last one
            for row in reshape[:-1]:
                for value in row:
                    self.file.write(f"0x{value:02x}, ")
                self.file.write("\n\t")

            # write the last line
            for value in reshape[-1][:last_row_size]:
                self.file.write(f"0x{value:02x}, ")

            if append_guard:
                # append a guard byte
                self.file.write("\n0")

            self.file.write("\n};")

            # write the size of the array as a define
            if size_var_name:
                self.file.write(f"#define {size_var_name} {array.size}\n")

        else:
            # declare the array of bytes in the form
            # ```
            # var_name:
            #     .byte $00,$00,...
            # ```
            self.file.write(f"{var_name}:\n")

            # write each line as is except the last one
            for row in reshape[:-1]:
                # assembly doesn't allow trailing commas
                # so we have the handle them ourselves
                first = row[0]
                self.file.write(f"\t.byte ${first:02x}")
                for value in row[1:]:
                    self.file.write(f",${value:02x}")
                self.file.write("\n")

            # write the last line
            first = reshape[-1][0]
            self.file.write(f"\t.byte ${first:02x}")
            for value in reshape[-1][1:last_row_size]:
                self.file.write(f",${value:02x}")
            self.file.write("\n")

            if append_guard:
                # append a guard byte
                self.file.write("\t.byte $00\n")

            # write the size of the array as a define
            if size_var_name:
                self.file.write(f"{size_var_name} = {array.size}\n")


if __name__ == "__main__":
    print("Library for generating code")
