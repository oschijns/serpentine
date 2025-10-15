# Utilities common to all assembly implementations

from collections.abc import Callable

# Process a line of assembly and convert it into a wiz instruction.
def proc_line(
        indent    : int,
        line      : str,
        prefix    : str, 
        template  : str = '{}', 
        transform : Callable[[str], str] = lambda x: x,
        comment   : str = ';'
    ) -> str|None:

    # Does the line match the expected prefix?
    if line.lower().startswith(prefix):
        # split off the comment if any
        head, _, tail = line.partition(comment)

        # Strip off the prefix from the beginning of the line.
        # Pass the remaining text to the transformation function to get a new set
        # of tokens. Then pass it to the template to complete the instruction.
        rm = len(prefix)
        tokens = transform(head[rm:].strip())
        inst = template.format(tokens)

        # Set indentation
        tab = ' ' * indent

        # Add the inline comment if there was any
        return f'{tab}{inst} {{# {tail} #}}\n' if tail else f'{tab}{inst}\n'
    else:
        return None


# Find the indentation level of a line
def get_indent(line: str, tabsize: int = 4) -> int:
    s = line.expandtabs(tabsize)
    return 0 if s.isspace() else len(s) - len(s.lstrip())
