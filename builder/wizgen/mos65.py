"""
    Assembly parser and converter for 6502 family processors
"""


_INST_MOS6502 = {
    # Add memory to accumulator with carry
    'adc': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', 'a +#= *(*(({zp} + x) as *u16) as *u8);'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', 'a +#= *(*(({zp} as *u16) + y) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , 'a +#= *(({addr} + x) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , 'a +#= *(({addr} + y) as *u8);'),
        (r'(?P<val>.+)'                    , 'a +#= {val};')
    ],

    # AND memory with accumulator
    'and': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', 'a &= *(*(({zp} + x) as *u16) as *u8);'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', 'a &= *(*(({zp} as *u16) + y) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , 'a &= *(({addr} + x) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , 'a &= *(({addr} + y) as *u8);'),
        (r'(?P<val>.+)'                    , 'a &= {val};')
    ],

    # Shift left one bit (memory or accumulator)
    'asl': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) <<= 1;'),
        (r'(?P<val>.+)'            , '{val} <<= 1;')
    ],

    # Branch on carry clear
    'bcc': (r'(?P<addr>.+)', 'goto ({addr}) if !carry;'),

    # Branch on carry set
    'bcs': (r'(?P<addr>.+)', 'goto ({addr}) if carry;'),

    # Branch on result zero
    'beq': (r'(?P<addr>.+)', 'goto ({addr}) if zero;'),

    # Test bits in memory with accumulator
    'bit': (r'(?P<val>.+)', 'bit({val});'),

    # Branch on result minus
    'bmi': (r'(?P<addr>.+)', 'goto ({addr}) if negative;'),

    # Branch on result not zero
    'bne': (r'(?P<addr>.+)', 'goto ({addr}) if !zero;'),

    # Branch on result plus
    'bpl': (r'(?P<addr>.+)', 'goto ({addr}) if !negative;'),

    # Force break
    'brk': 'irqcall(0);',

    # Branch on overflow clear
    'bvc': (r'(?P<addr>.+)', 'goto ({addr}) if !overflow;'),

    # Branch on overflow set
    'bvs': (r'(?P<addr>.+)', 'goto ({addr}) if overflow;'),

    # Clear carry flag
    'clc': 'carry = false;',

    # Clear decimal mode
    'cld': 'decimal = false;',

    # Clear interrupt disable status
    'cli': 'nointerrupt = false;',

    # Clear overflow flag
    'clv': 'overflow = false;',

    # Compare memory and accumulator
    'cmp': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', 'cmp(a, *(*(({zp} + x) as *u16) as *u8));'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', 'cmp(a, *(*(({zp} as *u16) + y) as *u8));'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , 'cmp(a, *(({addr} + x) as *u8));'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , 'cmp(a, *(({addr} + y) as *u8));'),
        (r'(?P<val>.+)'                    , 'cmp(a, {val});')
    ],

    # Compare memory and index X
    'cpx': (r'(?P<val>.+)', 'cmp(x, {val});'),

    # Compare memory and index Y
    'cpy': (r'(?P<val>.+)', 'cmp(y, {val});'),

    # Decrement memory by one
    'dec': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', '-- *(({addr} + x) as *u8);'),
        (r'(?P<val>.+)'            , '--({val});')
    ],

    # Decrement index X by one
    'dex': '--x;',

    # Decrement index Y by one
    'dey': '--y;',

    # XOR memory with accumulator
    'eor': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', 'a ^= *(*(({zp} + x) as *u16) as *u8);'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', 'a ^= *(*(({zp} as *u16) + y) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , 'a ^= *(({addr} + x) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , 'a ^= *(({addr} + y) as *u8);'),
        (r'(?P<val>.+)'                    , 'a ^= {val};')
    ],

    # Increment memory by one
    'inc': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', '++ *(({addr} + x) as *u8);'),
        (r'(?P<val>.+)'            , '++({val});')
    ],

    # Increment index X by one
    'inx': '++x;',

    # Increment index Y by one
    'iny': '++y;',

    # Jump to new location
    'jmp': [
        (r'\(\s*(?P<addr>.+)\s*\)', 'goto *(({addr}) as *u8);'),
        (r'(?P<addr>.+)'          , 'goto ({addr});')
    ],

    # Jump to new location saving return address
    'jsr': (r'(?P<func>.+)', '{func}();'),

    # Load accumulator with memory
    'lda': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', 'a = *(*(({zp} + x) as *u16) as *u8);'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', 'a = *(*(({zp} as *u16) + y) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , 'a = *(({addr} + x) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , 'a = *(({addr} + y) as *u8);'),
        (r'(?P<val>.+)'                    , 'a = {val};')
    ],

    # Load index X with memory
    'ldx': [
        (r'(?P<addr>.+)\s*,\s*[Yy]', 'x = *(({addr} + y) as *u8);'),
        (r'(?P<val>.+)'            , 'x = {val};')
    ],

    # Load index Y with memory
    'ldy': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', 'y = *(({addr} + x) as *u8);'),
        (r'(?P<val>.+)'            , 'y = {val};')
    ],

    # Shift right one bit (memory or accumulator)
    'lsr': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) >>>= 1;'),
        (r'(?P<val>.+)'            , '{val} >>>= 1;')
    ],

    # No operation
    'nop': 'nop();',

    # OR memory with accumulator
    'ora': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', 'a |= *(*(({zp} + x) as *u16) as *u8);'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', 'a |= *(*(({zp} as *u16) + y) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , 'a |= *(({addr} + x) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , 'a |= *(({addr} + y) as *u8);'),
        (r'(?P<val>.+)'                    , 'a |= {val};')
    ],

    # Push accumulator on stack
    'pha': 'push(a);',

    # Push processor status on stack
    'php': 'push(p);',

    # Pull accumulator from stack
    'pla': 'a = pop();',

    # Pull processor status from stack
    'plp': 'p = pop();',

    # Rotate one bit left (memory or accumulator)
    'rol': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) <<<<#= 1;'),
        (r'(?P<val>.+)'            , '{val} <<<<#= 1;')
    ],

    # Rotate one bit right (memory or accumulator)
    'ror': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) >>>>#= 1;'),
        (r'(?P<val>.+)'            , '{val} >>>>#= 1;')
    ],

    # Return from interrupt
    'rti': 'irqreturn;',

    # Return from subroutine
    'rts': 'return;',

    # Subtract memory from accumulator with borrow
    'sbc': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', 'a -#= *(*(({zp} + x) as *u16) as *u8);'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', 'a -#= *(*(({zp} as *u16) + y) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , 'a -#= *(({addr} + x) as *u8);'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , 'a -#= *(({addr} + y) as *u8);'),
        (r'(?P<val>.+)'                    , 'a -#= {val};')
    ],

    # Set carry flag
    'sec': 'carry = true;',

    # Set decimal mode
    'sed': 'decimal = true;',

    # Set interrupt disable status
    'sei': 'nointerrupt = true;',

    # Store accumulator in memory
    'sta': [
        (r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)', '*(*(({zp} + x) as *u16) as *u8) = a;'),
        (r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]', '*(*(({zp} as *u16) + y) as *u8) = a;'),
        (r'(?P<addr>.+)\s*,\s*[Xx]'        , '*(({addr} + x) as *u8) = a;'),
        (r'(?P<addr>.+)\s*,\s*[Yy]'        , '*(({addr} + y) as *u8) = a;'),
        (r'(?P<val>.+)'                    , '{val} = a;')
    ],

    # Store index X in memory
    'stx': [
        (r'(?P<addr>.+)\s*,\s*[Yy]', '*(({addr} + y) as *u8) = x;'),
        (r'(?P<val>.+)'            , '{val} = x;')
    ],

    # Store index Y in memory
    'sty': [
        (r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) = y;'),
        (r'(?P<val>.+)'            , '{val} = y;')
    ],

    # Transfer accumulator to index X
    'tax': 'x = a;',

    # Transfer accumulator to index Y
    'tay': 'y = a;',

    # Transfer stack pointer to index X
    'tsx': 'x = s;',

    # Transfer index X to accumulator
    'txa': 'a = x;',

    # Transfer index X to stack pointer
    'txs': 's = x;',

    # Transfer index Y to accumulator
    'tya': 'a = y;',
}

_INST_MOS65C02 = _INST_MOS6502 | {
#a = *(*({0..255} as *u16) as *u8)
#a += *(*({0..255} as *u16) as *u8)
#a +#= *(*({0..255} as *u16) as *u8)
#a -= *(*({0..255} as *u16) as *u8)
#a -#= *(*({0..255} as *u16) as *u8)
#a |= *(*({0..255} as *u16) as *u8)
#a &= *(*({0..255} as *u16) as *u8)
#a ^= *(*({0..255} as *u16) as *u8)
#*(*({0..255} as *u16) as *u8) = a
#cmp(a, *(*({0..255} as *u16) as *u8))
#
#bit({0..255})
#bit(*(({0..255} + x) as *u8))
#bit(*(({0..65535} + x) as *u8))
#
#++a
#--a
#
#goto {-128..127}
#^goto {0..65535}
#
#goto *(({0..65535} + x) as *u16)
#
#push(x)
#push(y)
#
#x = pop()
#y = pop()
#
#*({0..255} as *u8) = 0
#*(({0..255} + x) as *u8) = 0
#*({0..65535} as *u8) = 0
#*(({0..65535} + x) as *u8) = 0
#
#test_and_reset(*({0..255} as *u8))
#test_and_reset(*({0..65535} as *u8))
#
#test_and_set(*({0..255} as *u8))
#test_and_set(*({0..65535} as *u8))
}

_INST_ROCKWELL65C02 = _INST_MOS65C02 | {
#goto {-128..127} if *({0..255} as *u8) $ {0..7}
#goto {-128..127} if !(*({0..255} as *u8)) $ {0..7}
#^goto {0..65535} if *({0..255} as *u8) $ {0..7}
#^goto {0..65535} if !(*({0..255} as *u8)) $ {0..7}
#
#*({0..255} as *u8) $ {0..7} = false
#*({0..255} as *u8) $ {0..7} = true
}

_INST_WDC65C02 = _INST_ROCKWELL65C02 | {
#stop_until_reset()
#wait_until_interrupt()
}

_INST_HUC6280 = _INST_ROCKWELL65C02 | {
#a = 0
#x = 0
#y = 0
#
#turbo_speed = false
#turbo_speed = true
#
#swap(a, x)
#swap(a, y)
#swap(x, y)
#
#*(x as *u8) += {0..255}
#*(x as *u8) += *({0..255} as *u8)
#*(x as *u8) += *(({0..255} + x) as *u8)
#*(x as *u8) += *(*(({0..255} + x) as *u16) as *u8)
#*(x as *u8) += *(*(({0..255} as *u16) + y) as *u8)
#*(x as *u8) += *({0..65535} as *u8)
#*(x as *u8) += *(({0..65535} + x) as *u8)
#*(x as *u8) += *(({0..65535} + y) as *u8)
#
#*(x as *u8) +#= {0..255}
#*(x as *u8) +#= *({0..255} as *u8)
#*(x as *u8) +#= *(({0..255} + x) as *u8)
#*(x as *u8) +#= *(*(({0..255} + x) as *u16) as *u8)
#*(x as *u8) +#= *(*(({0..255} as *u16) + y) as *u8)
#*(x as *u8) +#= *({0..65535} as *u8)
#*(x as *u8) +#= *(({0..65535} + x) as *u8)
#*(x as *u8) +#= *(({0..65535} + y) as *u8)
#
#*(x as *u8) |= {0..255}
#*(x as *u8) |= *({0..255} as *u8)
#*(x as *u8) |= *(({0..255} + x) as *u8)
#*(x as *u8) |= *(*(({0..255} + x) as *u16) as *u8)
#*(x as *u8) |= *(*(({0..255} as *u16) + y) as *u8)
#*(x as *u8) |= *({0..65535} as *u8)
#*(x as *u8) |= *(({0..65535} + x) as *u8)
#*(x as *u8) |= *(({0..65535} + y) as *u8)
#
#*(x as *u8) &= {0..255}
#*(x as *u8) &= *({0..255} as *u8)
#*(x as *u8) &= *(({0..255} + x) as *u8)
#*(x as *u8) &= *(*(({0..255} + x) as *u16) as *u8)
#*(x as *u8) &= *(*(({0..255} as *u16) + y) as *u8)
#*(x as *u8) &= *({0..65535} as *u8)
#*(x as *u8) &= *(({0..65535} + x) as *u8)
#*(x as *u8) &= *(({0..65535} + y) as *u8)
#
#*(x as *u8) ^= {0..255}
#*(x as *u8) ^= *({0..255} as *u8)
#*(x as *u8) ^= *(({0..255} + x) as *u8)
#*(x as *u8) ^= *(*(({0..255} + x) as *u16) as *u8)
#*(x as *u8) ^= *(*(({0..255} as *u16) + y) as *u8)
#*(x as *u8) ^= *({0..65535} as *u8)
#*(x as *u8) ^= *(({0..65535} + x) as *u8)
#*(x as *u8) ^= *(({0..65535} + y) as *u8)
#
#vdc_select = {0..255}
#vdc_data_l = {0..255}
#vdc_data_h = {0..255}
#
#transfer_alternate_to_increment({0..65535}, {0..65535}, {0..65535})
#transfer_increment_to_alternate({0..65535}, {0..65535}, {0..65535})
#transfer_decrement_to_decrement({0..65535}, {0..65535}, {0..65535})
#transfer_increment_to_increment({0..65535}, {0..65535}, {0..65535})
#transfer_increment_to_fixed({0..65535}, {0..65535}, {0..65535})
#
#mpr_set({0..255}, a)
#mpr0 = a
#mpr1 = a
#mpr2 = a
#mpr3 = a
#mpr4 = a
#mpr5 = a
#mpr6 = a
#mpr7 = a
#a = mpr0
#a = mpr1
#a = mpr2
#a = mpr3
#a = mpr4
#a = mpr5
#a = mpr6
#a = mpr7
#
#tst({0..255}, *({0..255} as *u8))
#tst({0..255}, *(({0..255} + x) as *u8))
#tst({0..255}, *(({0..65535} + x) as *u8))
#tst({0..255}, *(({0..65535} + x) as *u8))
}

_INST_WDC65C816 = {
# TODO
}


_INST_SPC700 = _INST_MOS6502 | {
# TODO some instructions were removed from MOS6502
}