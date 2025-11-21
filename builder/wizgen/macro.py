"""
    Macro parser
"""

from asm_parser import RuleMacro


# .music_data_ptr = famistudio_ptr0

# Preprocessing macros
_MACRO_COMMON = [
    # Variable assignment
    RuleMacro(
        r'^(?P<var>[a-zA-Z_]\w*)\s*=\s*(?P<value>.+)$', 
        r'{{% set {var} = ({value}) %}}'
    ),

    # Convert error message to Python print statement
    RuleMacro(r'^\.error\s+(?P<cond>.+)$' , r'{{% print({cond}) %}}'),

    # Conditional assembly macros
    RuleMacro(r'^\.if\s+(?P<cond>.+)$'    , r'{{% if ({cond}) %}}'),
    RuleMacro(r'^\.elseif\s+(?P<cond>.+)$', r'{{% elif ({cond}) %}}'),
    RuleMacro(r'^\.else$'                 , r'{{% else %}}'),
    RuleMacro(r'^\.endif$'                , r'{{% endif %}}'),

    # Specific if macros
    RuleMacro(r'^\.ifdef\s+(?P<cond>.+)$' , r'{{% if ({cond}) is not none %}}'),
    RuleMacro(r'^\.ifndef\s+(?P<cond>.+)$', r'{{% if ({cond}) is none %}}'),
]


# Preprocessing macros for ASM6
_MACRO_ASM6 = _MACRO_COMMON + [
    # Base
    RuleMacro(r'^\.base\s+(?P<name>.+)$', r'{{% if true %}}'),

    # Enum macro
    RuleMacro(r'^\.enum\s+(?P<name>.+)$', r'{{% if true %}}'),
    RuleMacro(r'^\.ende\s*$'            , r'{{% endif %}}'),

    # Sequence of bytes macro
    RuleMacro(r'^\.dsb\s+(?P<bytes>.+)$'  , r'{bytes},'),

    # TODO @label
]


# Preprocessing macros for CA65
_MACRO_CA65 = _MACRO_COMMON + [
    # Convert error message to Python print statement
    RuleMacro(
        r'^\.if\s+\.xmatch\(\s*\.string\(\s*(?P<name1>.+)\)\s*,\s*"(?P<name2>.+)"\s*\)$',
        r'{{% if ({name1}) %}}'
    ),

    # Sequence of bytes macro
    RuleMacro(r'^\.res\s+(?P<bytes>.+)$'  , r'{bytes},'),

    # TODO @label
]


# Preprocessing macros for NESASM
_MACRO_NESASM = _MACRO_COMMON + [

    # TODO .label

]


# Preprocessing macros for SDAS
_MACRO_SDAS = _MACRO_COMMON + [

    # Declare a local label
    RuleMacro(r'^\.local\s+\.(?P<label>.+)$' , r'{{% set {label} = none %}}'),

    # Convert error message to Python print statement
    RuleMacro(r'^\.error\s+(?P<cond>.+)$' , r'{{% print({cond}) %}}'),
    RuleMacro(r'^\.msg\s+(?P<cond>.+)$'   , r'{{% print({cond}) %}}'),

    # Conditional comparisons
    RuleMacro(r'^\.ifeq\s+(?P<cond>.+)$', r'{{% if ({cond}) == 0 %}}'),
    RuleMacro(r'^\.ifge\s+(?P<cond>.+)$', r'{{% if ({cond}) >= 0 %}}'),
    RuleMacro(r'^\.ifgt\s+(?P<cond>.+)$', r'{{% if ({cond}) > 0 %}}'),
    RuleMacro(r'^\.ifle\s+(?P<cond>.+)$', r'{{% if ({cond}) <= 0 %}}'),
    RuleMacro(r'^\.iflt\s+(?P<cond>.+)$', r'{{% if ({cond}) < 0 %}}'),

    # TODO *.label
]
