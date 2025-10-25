"""
    Generic Assembly Parser
"""

import re

# Conversion rule for a specific instruction
class RuleInst:

    # Construct a rule to convert an instruction
    def __init__(self,
        regex     : str,
        template  : str,
        j2_wraps  : list[str] = [],
        registers : list[str] = []
    ):
        """
        Create a rule to convert an assembly instruction to wiz format.

        @type  regex: str
        @param regex: Assembly instruction to match

        @type  template: str
        @param template: Formatting string to generate the corresponding wiz statement

        @type  j2_wraps: list[str]
        @param j2_wraps: Specify if some matching group should be wrapped in Jinja block

        @type  registers: list[str]
        @param registers: Specify if some matching group represent registers
        """

        self.regex     = re.compile(regex)
        self.template  = template
        self.j2_wraps  = set(j2_wraps)
        self.registers = set(registers)


    # Transform the instruction
    def convert(self, operands: str) -> str | None:
        # try to match the provided operands with the regex template
        result = self.regex.match(operands)
        if result is None: return None

        # get the result as a dictionary for manipulation
        groups = result.groupdict()

        # apply lowering if needed
        for key in groups:
            if key in self.registers:
                groups[key] = groups[key].lower()
            elif key in self.j2_wraps:
                groups[key] = f'({{{{ {groups[key]} }}}})'

        return self.template.format(**groups)


# Conversion rule for an instruction identified by its mnemonic
class RuleMnemo:

    # Construct a rule to convert an instruction
    def __init__(self, name: str, rules: str | list[RuleInst]):
        """
        Create a rule to convert an assembly instruction to wiz format.

        @type  name: str
        @param name: Mnemonic corresponding to this ruleset

        @type  rules: str | list[RuleInst]
        @param rules: Conversion rule, which can be either:
        - a simple instruction string to replace the original instruction
        - a list of (regex, template) pairs to try in sequence
        """

        self.name = name.lower()

        # Simple instruction replacement
        if isinstance(rules, str):
            self.rules  = None
            self.output = rules

        # Multiple regex-template pairs to try in sequence
        elif isinstance(rules, list):
            self.rules = rules
            self.output = None

        # Unsupported rule type
        else:
            raise Exception(f"Invalid instruction rule type: {type(rules)}")


    # Transform the instruction
    def convert(self, operands: str) -> str:
        # Simply replace the instruction by the other
        if self.rules is None:
            return self.output

        # Try each rule in sequence until one matches
        else:
            for rule in self.rules:
                result = rule.convert(operands)
                if result is not None:
                    return result

            # no match found
            raise Exception(f"Operands do not match the expected format: {operands}")


# Assembly parser
class AsmParser:

    # Regex for reading a identifier
    _IDENT = re.compile(r'^([a-zA-Z_]\w*)')

    # Regex for extracting a mnemonic from an instruction line
    _MNEMO = re.compile(r'^([a-zA-Z][a-zA-Z\.]*)')


    # Create a configuration for parsing standard assembly syntax
    def __init__(self, rules: list[RuleMnemo], tabsize: int = 4):
        """
        Create a configuration for parsing regular assembly 
        syntax and converting it to wiz format.

        @type  rules: list[RuleMnemo]
        @param rules: Define conversion rules for each mnemonic

        @type  tabsize: int (default 4)
        @param tabsize: Number of spaces per tab character
        """

        # set tab size
        self.tabsize : int = tabsize

         # variables encountered during parsing
        self.variables : set[str] = set()

        # process the rules
        self.rules: dict[str, RuleMnemo] = {}
        for rule in rules:
            self.rules[rule.name] = rule


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
                rule: RuleMnemo = self.rules[mnemo]

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

