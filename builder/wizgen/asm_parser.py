"""
    Generic Assembly Parser
"""

import re
from typing import Any, Self, Callable


# Conversion rule for an instruction
class InstRule:

    # Construct a rule to convert an instruction
    def __init__(self, template: str, regex: str | None = None):
        # Compile the regex if provided
        self.regex = None if regex is None else re.compile(regex)

        # Store the template
        self.template: str = template

    # Transform the instruction
    def convert(self, operands: str) -> str:
        # Simply replace the instruction by the other
        if self.regex is None:
            return self.template

        # If a regex is defined, match the operands
        else:
            result = self.regex.match(operands)
            if result is None:
                raise Exception(f"Operands do not match the expected format: {operands}")

            # extract the parameters and format the instruction
            return self.template.format(**result.groupdict())


# Assembly parser
class AsmParser:

    # Regex for reading a identifier
    _IDENT = re.compile(r'^([a-zA-Z_][\w]*)')

    # Regex for extracting a mnemonic from an instruction line
    _MNEMO = re.compile(r'^([a-zA-Z\.]+)')

    # Create a configuration for parsing standard assembly syntax
    def __init__(self, 
        rules   : dict[str, str | InstRule],
        tabsize : int = 4):

        # set tab size
        self.tabsize : int = tabsize

         # variables encountered during parsing
        self.variables : set[str] = set()

        # process the rules
        self.rules: dict[str, InstRule] = {}
        for mnemo, rule in rules.items():
            mnemo = mnemo.lower()

            # instantiate a rule if needed
            if not isinstance(rule, InstRule):
                rule = InstRule(rule)
            self.rules[mnemo] = rule

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

