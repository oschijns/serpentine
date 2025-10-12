# Parser for FamiStudio text file format

import re
import numpy
from io import TextIOWrapper
from typing_extensions import Self

# Reference:
# https://famistudio.org/doc/export/#famistudio-text


# Read a line and extract the object type and its attributes to populate a dictionary
class LineReader:

    # construct regex parsers
    def __init__(self) -> None:
        self.pattern_node = re.compile(r'\w+')
        self.pattern_attr = re.compile(r'(\w+)="((""|[^"])*)"')


    # read a file line by line and return a list of nodes with their attributes
    def read_file(self, file: TextIOWrapper) -> list[tuple[str, dict[str, str]]]:
        lines = []
        for line in file:
            if entry := self.read_line(line):
                lines.append(entry)
        return lines


    # read a single line and produce a dictionary
    def read_line(self, line: str) -> tuple[str, dict[str, str]] | None:
        if found := self.pattern_node.search(line):

            # compose a dictionary containing the attributes
            attributes = {}
            for attr in self.pattern_attr.finditer(line, found.end(0)):
                attributes[attr.group(1)] = attr.group(2).replace('""', '\\"')

            # return the node type and its attributes
            return (found.group(0), attributes)
        else:
            return None


# A node of a tree
class Node:

    # generate a node with a type name, attributes and definition
    def __init__(self, name: str, attr: dict[str, str], relations: list[str]) -> None:
        # the parent of this node
        self.parent: Self | None = None

        # store the type name and attributes for this node
        self.name = name
        self.attributes = attr

        # create a list for each type of children expected
        self.children = {}
        for key in relations:
            self.children[key] = []


    # add a child node to this node
    # return true if the node was successfully added as a child
    def add_child(self, child: Self) -> bool:

        # check if the node is of an expected type
        if child.name in self.children:

            # link both node as parent and child
            self.children[child.name].append(child)
            child.parent = self
            return True

        else:
            return False


    # display the content of the node in readable format
    def __repr__(self) -> str:
        return self._to_string(0)


    # helper function to display the node with indentation
    def _to_string(self, indent: int) -> str:
        data: list[str] = ['{} {}'.format(self.name, self.attributes)]
        for children in self.children.values():
            for child in children:
                data.append(child._to_string(indent + 1))
        head = '\n' + ('\t' * indent)
        return head.join(data)


# Generate a tree structure from the entries
class TreeGenerator:

    # define a tree to determine the hierarchy of nodes
    def __init__(self) -> None:
        # define the relations parent-child of the nodes
        tree_structure = {
            'Project': {
                'DPCMSample': None,
                'DPCMMapping': None,
                'Instrument': {
                    'Envelope': None,
                },
                'Song': {
                    'PatternCustomSettings': None,
                    'Channel': {
                        'Pattern': {
                            'Note': None,
                        },
                        'PatternInstance': None,
                    },
                },
            }
        }

        # for each node type, specify the expected children types
        self.relations = {}
        self._get_relations('Project', tree_structure['Project'])


    # get the relations
    def _get_relations(self, node: str, entries: dict | None) -> None:
        children = []

        # does the node have children?
        if isinstance(entries, dict):
            # if so add them to the relations map
            for (key, value) in entries.items():
                children.append(key)
                self._get_relations(key, value)
        self.relations[node] = children


    # display the relations rules
    def __repr__(self) -> str:
        data: list[str] = []
        for (parent, children) in self.relations.items():
            data.append('{}: {}'.format(parent, children))
        return '\n'.join(data)


    # apply the hierachy template to the entries provided
    def hierarchize(self, entries: list[tuple[str, dict[str, str]]]) -> Node:
        root_node: Node | None = None
        cached_node: Node | None = None

        # iterate over each of the entries
        for (entry_type, entry_attr) in entries:

            # create a node given the current entry
            node = Node(entry_type, entry_attr, self.relations[entry_type])

            # we already cached a node
            if isinstance(cached_node, Node):
                # try to add the new node to the cached node or any of its ancestors
                while not cached_node.add_child(node):
                    cached_node = cached_node.parent
                    if cached_node is None:
                        raise Exception("Could not find where to store the entry in the tree:\n{}".format(node))
                cached_node = node

            # if it is the first node, it is the root
            else:
                root_node = node
                cached_node = node

        # At that point, we are expecting to return the root of the tree generated
        if root_node is None:
            raise Exception("Text file does not contain a FamiStudio project")
        else:
            return root_node


# Read a string representing a note to get the Hertz
class NoteReader:

    # construct a note reader
    def __init__(self) -> None:
        self.pattern = re.compile("^[A-G]#?[1-8]$")

        # generate a look up table to store frequency values
        octaves_count = 8
        notes_per_octave = 12
        self.frequencies = numpy.zeros((octaves_count, notes_per_octave), dtype=numpy.float64)

        # for each note in the octaves, compute the corresponding frequency
        oct_start = 55.0
        for o in range(octaves_count):
            for n in range(notes_per_octave):
                self.frequencies[o, n] = oct_start * (2.0 ** (n / float(notes_per_octave)))
            oct_start *= 2.0


    # read a note and get its value in Hertz
    def read_node(self, note: str) -> float:
        if not self.pattern.match(note):
            raise Exception("Could not read the note {}".format(note))

        # convert the letter into a pitch and the number into an octave
        n = note.encode()
        pitch = (n[0] - 0x41) * 2 # 'A' = 0x41
        octave = n[-1] - 0x31 # '1' = 0x31

        # is there a '#' in the note ?
        if len(note) == 3:
            pitch += 1

        # recover the corresponding frequency value
        return self.frequencies[octave, pitch]


# convert the frequency into binary for NTSC platform
# https://www.nesdev.org/wiki/Celius_NTSC_table
def encode_ntsc(frequency: float) -> int:
    return round((1790000.0 / frequency * 16.0) - 1.0)


# convert the frequency into binary for PAL platform
# https://www.nesdev.org/wiki/Celius_PAL_table
def encode_pal(frequency: float) -> int:
    return round((1662607.0 / frequency * 16.0) - 1.0)


line_reader = LineReader()
f = open('assets/ducktales.txt')
lines = line_reader.read_file(f)

gen = TreeGenerator()
print(gen)

try:
    root = gen.hierarchize(lines)
    print('Tree generated: {}'.format(root))
except Exception as e:
    print(e)
