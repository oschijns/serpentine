"""
    Generic Assembly Parser
"""

import re
from typing import Any, Self, Callable


# Conversion rule for an instruction
class InstRule:

    # Construct a rule to convert an instruction
    def __init__(self, rules: str | tuple[str, str] | list[tuple[str, str]]) -> None:
        # Simple instruction replacement
        if isinstance(rules, str):
            self.rules  = None
            self.output = rules

        # Single regex-template pair
        elif isinstance(rules, tuple):
            self.rules = [(re.compile(rules[0]), rules[1])]

        # Multiple regex-template pairs to try in sequence
        elif isinstance(rules, list):
            self.rules = [(re.compile(regex), temp) for regex, temp in rules]

        # Unsupported rule type
        else:
            raise Exception(f"Invalid instruction rule type: {type(rule)}")


    # Transform the instruction
    def convert(self, operands: str) -> str:
        # Simply replace the instruction by the other
        if self.rules is None:
            return self.output

        # Try each rule in sequence until one matches
        else:
            for regex, template in self.rules:
                result = regex.match(operands)

                # extract the parameters and format the instruction
                if result is not None:
                    return template.format(**result.groupdict())

            # no match found
            raise Exception(f"Operands do not match the expected format: {operands}")


# Assembly parser
class AsmParser:

    # Regex for reading a identifier
    _IDENT = re.compile(r'^([a-zA-Z_][\w]*)')

    # Regex for extracting a mnemonic from an instruction line
    _MNEMO = re.compile(r'^([a-zA-Z\.]+)')


    # Create a configuration for parsing standard assembly syntax
    def __init__(self, 
        rules   : dict[str, str | tuple[str, str] | list[tuple[str, str]]],
        tabsize : int = 4):
        """
        Create a configuration for parsing regular assembly 
        syntax and converting it to wiz format.

        @type  rules: dict[str, str | tuple[str, str] | list[tuple[str, str]]]
        @param rules: Mapping of mnemonics to conversion rules. 
        Each rule can be either:
        - a simple instruction
        - a regex template to match and apply to a formatting template
        - a list of such regex-formatting pair to try in sequence

        @type  tabsize: int (default 4)
        @param tabsize: Number of spaces per tab character
        """

        # set tab size
        self.tabsize : int = tabsize

         # variables encountered during parsing
        self.variables : set[str] = set()

        # process the rules
        self.rules: dict[str, InstRule] = {}
        for mnemo, rule in rules.items():
            self.rules[mnemo.lower()] = InstRule(rule)


    # Convert assembly instruction to wiz format
    def convert(self, line: str) -> str:
        indent, code, comment = self._preprocess(line)

        # Generate a line
        tab: str = ' ' * indent
        out: str = ''
        cmt_type: bool = False

        if code is not None:
            # Check if it is a preprocessor directive
            if code.startswith('.'):
                cmt_type = True

            # Or it is a variable definition
            elif '=' in code:
                cmt_type = True

                result = AsmParser._IDENT.match(code)
                if result is None:
                    raise Exception(f"Cannot parse variable definition: {code}")

                varname: str = result.group(1)
                self.variables.add(varname)

            # Otherwise, it is an instruction
            else:
                # extract the mnemonic
                result = AsmParser._MNEMO.match(code)
                if result is None:
                    raise Exception(f"Cannot parse instruction: {code}")
                mnemo = result.group(1).lower()

                # look up the rule
                if mnemo not in self.rules:
                    raise Exception(f"Unsupported instruction: {mnemo}")
                rule: InstRule = self.rules[mnemo]

                operands: str = code[len(mnemo):].strip()
                out = rule.convert(operands)

        # Generate the comment
        cmt: str = ''
        if comment is not None:
            cmt = f' {{# {comment} #}}' if cmt_type else f'// {comment}'

        return f'{tab}{out}{cmt}'


    # Strip comments and whitespace and get indentation level
    def _preprocess(self, line: str) -> tuple[int, str | None, str | None]:
        # get indentation level
        tmp   : str = line.expandtabs(self.tabsize)
        line  : str = line.strip()
        indent: int = 0 if tmp.isspace() else len(tmp) - len(line)

        # Strip comments
        code, _, comment = line.partition(';')

        # Clean up code and comment
        code = code.strip()
        if code == '':
            code = None
        if comment is not None:
            comment = comment.strip()

        # return the triplet
        if code is None and comment is None:
            return 0, None, None
        else:
            return indent, code, comment

