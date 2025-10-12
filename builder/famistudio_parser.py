#!/usr/bin/env python

"""
    Read FamiStudio text file format and convert it into JSON or YAML
"""

import re
import sys
import json
import yaml

from io             import TextIOWrapper
from dataclasses    import dataclass
from configargparse import ArgParser
from typing         import Any, Self, Callable

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


# Definition of a node in a tree graph
class NodeDef:

    # Regex expression to convert from PascalCase to snake_case
    _RENAME = re.compile(r'(?<!^)(?=[A-Z])')

    # Regex expression to identify a note
    _NOTE = re.compile("^[A-G]#?[1-8]$")

    # Definition of the node type
    def __init__(self,
        name       : str,
        attributes : dict[str, type | Callable[[str], Any]] = {},
        children   : list[Self] = [],
        rename     : str | None = None
    ):
        # Name of the node as definied in the document
        self.name: str = name

        # If an explicit rename was provided, use it.
        # Otherwise convert PascalCase into snake_case.
        self.new_name: str = (NodeDef.rename(name) + 's') if rename is None else rename

        # Associate attributes with a rename
        self.attributes: dict[str, tuple[str, Callable[[str], Any]]] = {}
        for aname, atype in attributes.items():

            # Generate a snake_case name
            new_name = NodeDef.rename(aname)

            # Convert an attribute value into the target type
            convert = lambda x: x
            if isinstance(atype, Callable): convert = atype
            elif atype == bool : convert = lambda x: x != 'False'
            elif atype == int  : convert = lambda x: int(x, 0)
            elif atype == float: convert = lambda x: float(x)
            elif atype == str  : convert = lambda x: str(x)
            else: raise Exception(f"Unsupported {atype} type for document structure definition")

            # Associate document name with target name and conversion function
            self.attributes[aname] = (new_name, convert)

        # Parent type node definition
        self.parent: Self | None = None

        # Identify the type of node by its name
        self.children: dict[str, Self] = {}
        for child in children:
            child.parent = self
            self.children[child.name] = child

    # Convert this node into a regular python dictionary
    def to_dict(self) -> dict[str, Any]:
        nodes = {}
        for name, child in self.children.items():
            nodes[name] = child.to_dict()

        return {
            'name'  : self.name,
            'attr'  : [k for k in self.attributes.keys()],
            'nodes' : nodes
        }

    # Convert PascalCase name into snake_case name
    @staticmethod
    def rename(name: str) -> str:
        return NodeDef._RENAME.sub('_', name).lower()

    # Color formatter
    @staticmethod
    def format_color(c: str) -> str:
        return f'#{c}'

    # Format a note to be simpler to process
    @staticmethod
    def format_note(n: str) -> str:
        if not NodeDef._NOTE.match(n):
            raise Exception("Could not read the note {}".format(n))
        elif len(n) == 2:
            return f'{n[0]}-{n[1]}'
        else:
            return n


# Specify the format of a famistudio text file
_DOCUMENT_FORMAT = NodeDef('Project', {
        'Version'   : str,
        'Expansion' : str,
        'TempoMode' : str,
        'Name'      : str,
        'Author'    : str,
        'Copyright' : str,
    }, [
        NodeDef('DPCMSample', {
            'Name' : str,
            'Data' : str,
        }, rename='dpcm_samples'),
        NodeDef('DPCMMapping', {
            'Note'   : str,
            'Sample' : str,
            'Pitch'  : int,
            'Loop'   : bool,
        }, rename='dpcm_mappings'),
        NodeDef('Instrument', {
            'Name'  : str,
            'Color' : NodeDef.format_color,
        }, [
            NodeDef('Envelope', {
                'Type'   : str,
                'Length' : int,
                'Values' : lambda s: [int(x,0) for x in s.split(',')],
            }),
        ]),
        NodeDef('Song', {
            'Name'              : str,
            'Color'             : NodeDef.format_color,
            'Length'            : int,
            'LoopPoint'         : int,
            'PatternLength'     : int,
            'BeatLength'        : int,
            'NoteLength'        : int,
            'Groove'            : int,
            'GroovePaddingMode' : str,
        }, [
            NodeDef('PatternCustomSettings', {
                'Time'              : int,
                'Length'            : int,
                'NoteLength'        : int,
                'Groove'            : int,
                'GroovePaddingMode' : str,
                'BeatLength'        : int,
            }),
            NodeDef('Channel', {
                'Type' : str,
            }, [
                NodeDef('Pattern', {
                    'Name'  : str,
                    'Color' : NodeDef.format_color,
                }, [
                    NodeDef('Note', {
                        'Time'         : int,
                        'Value'        : NodeDef.format_note,
                        'Duration'     : int,
                        'Instrument'   : str,
                        'VibratoSpeed' : int,
                        'VibratoDepth' : int,
                        'Volume'       : int,
                    }),
                ]),
                NodeDef('PatternInstance', {
                    'Time'    : int,
                    'Pattern' : str,
                }),
            ]),
        ]),
    ])


# A node of a tree
class Node:

    # Generate a node with a type name, attributes and definition
    def __init__(self,
        definition: NodeDef,
        attributes: dict[str, str],
    ):
        # Keep track of the initial definition of this node
        self.definition: NodeDef = definition

        # Store the type name and attributes for this node
        self.attributes: dict[str, Any] = {}
        for name, value_attr in attributes.items():
            if name in definition.attributes:
                rename, convert = definition.attributes[name]
                self.attributes[rename] = convert(value_attr)

        # The parent of this node
        self.parent: Self | None = None

        # Create a list for each type of children expected
        self.children: dict[str, tuple[NodeDef, list[Self]]] = {}
        for type_name, type_def in definition.children.items():
            self.children[type_name] = (type_def, [])

    # Print the definition
    def __repr__(self) -> str:
        f"{self.definition.name}"

    # Use this node to process the line return a new node generated from the entry
    def handle_entry(self, type_name: str, attr: dict[str, str]) -> Self:
        # Check if one of the children of this node can handle this entry
        if type_name in self.children:
            type_def, nodes = self.children[type_name]

            # Create a new node
            node = Node(type_def, attr)
            node.parent = self
            nodes.append(node)
            return node

        # This node cannot handle this entry, try processing with a parent node
        else:
            if self.parent is None:
                raise Exception(f"Unexpected node type {type_name}")
            return self.parent.handle_entry(type_name, attr)
    
    # Convert this node into a regular python dictionary
    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = self.attributes.copy()

        # convert children nodes into dictionaries too
        for type_def, nodes in self.children.values():
            out[type_def.new_name] = [n.to_dict() for n in nodes]
        
        return out


# Process the entries and return a tree graph
def process_entries(entries: list[tuple[str, dict[str, str]]]) -> Node:
    # Read the first entry
    root    = Node(_DOCUMENT_FORMAT, entries[0][1])
    current = root

    # Then process the rest
    for name, attr in entries[1:]:
        current = current.handle_entry(name, attr)

    # Return the generated graph
    return root


print(json.dumps(_DOCUMENT_FORMAT.to_dict(), indent=4))

line_reader = LineReader()
f = open('assets/ducktales.txt')
lines = line_reader.read_file(f)

root_node = process_entries(lines)

print(json.dumps(root_node.to_dict(), indent=4))
