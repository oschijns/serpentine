# From generic 6502 assembly to wiz syntax

import re
from processors.utils import proc_line


# Processor for MOS 6502 instruction set
class Mos6502:

    # Create a processor for MOS 6502
    def __init__(self, variant: str):
        match variant:
            case 'asm6':
                self.indexer = Indexer()
            case 'ca65':
                self.indexer = Indexer()
            case 'nesasm':
                self.indexer = Indexer(True)
            case 'sdas':
                self.indexer = Indexer(True)
        
        # Function to handle indexing
        ind = lambda x: self.indexer.convert(x)

        # table of matching between mnemonics and wiz statements
        self.instructions = [
            ('adc', 'a +#= {};'              , ind),    # Add memory to accumulator with carry
            ('and', 'a &= {};'               , ind),    # AND memory with accumulator
            ('asl', '{} <<= 1;'              , ind),    # Shift left one bit (memory or accumulator)
            ('bcc', 'goto ({}) if !carry;'   ),         # Branch on carry clear
            ('bcs', 'goto ({}) if carry;'    ),         # Branch on carry set
            ('beq', 'goto ({}) if zero;'     ),         # Branch on result zero
            ('bit', 'bit({});'               ),         # Test bits in memory with accumulator
            ('bmi', 'goto ({}) if negative;' ),         # Branch on result minus
            ('bne', 'goto ({}) if !zero;'    ),         # Branch on result not zero
            ('bpl', 'goto ({}) if !negative;'),         # Branch on result plus
            ('brk', 'irqcall(0);'            ),         # Force break
            ('bvc', 'goto ({}) if !overflow;'),         # Branch on overflow clear
            ('bvs', 'goto ({}) if overflow;' ),         # Branch on overflow set
            ('clc', 'carry = false;'         ),         # Clear carry flag
            ('cld', 'decimal = false;'       ),         # Clear decimal mode
            ('cli', 'nointerrupt = false;'   ),         # Clear interrupt disable status
            ('clv', 'overflow = false;'      ),         # Clear overflow flag
            ('cmp', 'cmp(a, {});'            , ind),    # Compare memory and accumulator
            ('cpx', 'cmp(x, {});'            , ind),    # Compare memory and index X
            ('cpy', 'cmp(y, {});'            , ind),    # Compare memory and index Y
            ('dec', '--({});'                , ind),    # Decrement memory by one
            ('dex', '--x;'                   ),         # Decrement index X by one
            ('dey', '--y;'                   ),         # Decrement index Y by one
            ('eor', 'a ^= {};'               , ind),    # XOR memory with accumulator
            ('inc', '++({});'                , ind),    # Increment memory by one
            ('inx', '++x;'                   ),         # Increment index X by one
            ('iny', '++y;'                   ),         # Increment index Y by one
            ('jmp', 'goto ({});'             , ind),    # Jump to new location
            ('jsr', '{}();'                  ),         # Jump to new location saving return address
            ('lda', 'a = {};'                , ind),    # Load accumulator with memory
            ('ldx', 'x = {};'                , ind),    # Load index X with memory
            ('ldy', 'y = {};'                , ind),    # Load index Y with memory
            ('lsr', '{} >>>= 1;'             , ind),    # Shift right one bit (memory or accumulator)
            ('nop', 'nop();'                 ),         # No operation
            ('ora', 'a |= {};'               , ind),    # OR memory with accumulator
            ('pha', 'push(a);'               ),         # Push accumulator on stack
            ('php', 'push(p);'               ),         # Push processor status on stack
            ('pla', 'a = pop();'             ),         # Pull accumulator from stack
            ('plp', 'p = pop();'             ),         # Pull processor status from stack
            ('rol', '{} <<<<#= 1;'           , ind),    # Rotate one bit left (memory or accumulator)
            ('ror', '{} >>>>#= 1;'           , ind),    # Rotate one bit right (memory or accumulator)
            ('rti', 'irqreturn;'             ),         # Return from interrupt
            ('rts', 'return;'                ),         # Return from subroutine
            ('sbc', 'a -#= {};'              , ind),    # Subtract memory from accumulator with borrow
            ('sec', 'carry = true;'          ),         # Set carry flag
            ('sed', 'decimal = true;'        ),         # Set decimal mode
            ('sei', 'nointerrupt = true;'    ),         # Set interrupt disable status
            ('sta', '{} = a;'                , ind),    # Store accumulator in memory
            ('stx', '{} = x;'                , ind),    # Store index X in memory
            ('sty', '{} = y;'                , ind),    # Store index Y in memory
            ('tax', 'x = a;'                 ),         # Transfer accumulator to index X
            ('tay', 'y = a;'                 ),         # Transfer accumulator to index Y
            ('tsx', 'x = s;'                 ),         # Transfer stack pointer to index X
            ('txa', 'a = x;'                 ),         # Transfer index X to accumulator
            ('txs', 's = x;'                 ),         # Transfer index X to stack pointer
            ('tya', 'a = y;'                 ),         # Transfer index Y to accumulator
        ]


    # Process a line of assembly
    def process(self, indent: int, line: str) -> str|None:
        for inst in self.instructions:
            # get the reprocessing function if one was defined
            reproc = inst[2] if len(inst) >= 3 else lambda x: x

            # Try to process the line using the given rule
            if tokens := proc_line(indent, line, inst[0], inst[1], reproc):
                return tokens
        
        if line.strip()[-1] == ':':
            # label
            label = line.strip()[:-1]
            tab = ' ' * indent
            return f'{tab}{label}:\n'

        # Not recognized
        return None


# Indexing syntax vary between ASM6, CA65, NesAsm and SDAS
# lda #imm
# lda zp
# lda zp  , x
# lda abs
# lda abs , x
# lda abs , y
# lda (zp , x)
# lda (zp), y
class Indexer:

    # Indexing use either parenthesis or brackets
    def __init__(self, brackets: bool = False):
        if brackets:
            self.ind   = re.compile(r'^([\w\s\+\-]+)\s*,\s*([xy])$')
            self.ind_x = re.compile(r'^\[(\w+)\s*,\s*x\]$')
            self.ind_y = re.compile(r'^\[(\w+)\]\s*,\s*y$')
        else:
            self.ind   = re.compile(r'^([\w\s\+\-]+)\s*,\s*([xy])$')
            self.ind_x = re.compile(r'^\((\w+)\s*,\s*x\)$')
            self.ind_y = re.compile(r'^\((\w+)\)\s*,\s*y$')

    # Convert indexing expression
    def convert(self, tokens: str) -> str:
        # Some assembly language use '$' for hexadecimal literal
        # For low byte and high byte access, replace '<' by '<:' and '>' by '>:'
        tokens = tokens.replace('$', '0x').replace('<', '<:').replace('>', '>:')

        # Immediate mode
        if tokens.startswith('#'):
            return tokens[1:]

        # (Indexed by X) Indirect 
        elif result := self.ind_x.match(tokens):
            memory = result.group(1)
            return f'*(*(({memory} + x) as *u16) as *u8)'

        # (Indirect) Indexed by Y
        elif result := self.ind_y.match(tokens):
            memory = result.group(1)
            return f'*((*({memory} as *u16) + y) as *u8)'

        # Indirect indexing
        elif result := self.ind.match(tokens):
            memory = result.group(1)
            index  = result.group(2)
            return f'*(({memory} + {index}) as *u8)'

        # Indirect indexing
        else:
            return f'*(({tokens}) as *u8)'

