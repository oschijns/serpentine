
import numpy
import tool.code_gen


def main():
    array = numpy.random.randint(0, 256, size=(8, 16), dtype=numpy.uint8)

    file_c = tool.code_gen.TargetFile("gen/test1.c", 'C')
    file_c.write_array("test1", array, values_per_row=12)
    file_c = None

    file_asm = tool.code_gen.TargetFile("gen/test2.s", 'asm')
    file_asm.write_array("test2", array, values_per_row=8)
    file_asm = None


if __name__ == "__main__":
    main()