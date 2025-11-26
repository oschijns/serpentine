# generator util
# generator for source files

import numpy


# generate a .wiz file
def generate_wiz(data, path, namespace=None, bank="program", variable="sequence", comment=None):
    with open(path, 'w+') as file:
        # constitute an array of bytes
        arrays = []
        for index, bytes in enumerate(data):
            array = []
            for byte in bytes:
                array.append(f"0x{byte:02x}")
            arrays.append(f"const {variable}{index} : [u8] = [{', '.join(array)}];")

        # generate the source
        source = "in {} {{\n\t{}\n}}".format(bank, '\n\t'.join(arrays))

        # add the namespace if specified
        if namespace is not None:
            source = "namespace {} {{\n{}\n}}".format(namespace, source.replace('\n', '\n\t'))

        # add the comment if specified
        if comment is not None:
            source = "/*\n{}\n*/\n{}".format(comment.replace('\n', '\n\t'), source)

        # write the source
        file.write(source)