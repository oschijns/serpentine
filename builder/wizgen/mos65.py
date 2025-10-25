"""
    Assembly parser and converter for 6502 family processors
"""

from asm_parser import RuleMnemo, RuleInst

_INST_MOS6502 = [
    # Add memory to accumulator with carry
    RuleMnemo('adc', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , 'a +#= *(*(({zp} + x) as *u16) as *u8);', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , 'a +#= *(*(({zp} as *u16) + y) as *u8);', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', 'a +#= *(({addr} + {reg}) as *u8);'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , 'a +#= {val};'                          , ['val' ])
    ]),

    # AND memory with accumulator
    RuleMnemo('and', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , 'a &= *(*(({zp} + x) as *u16) as *u8);', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , 'a &= *(*(({zp} as *u16) + y) as *u8);', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', 'a &= *(({addr} + {reg}) as *u8);'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , 'a &= {val};'                          , ['val' ])
    ]),

    # Shift left one bit (memory or accumulator)
    RuleMnemo('asl', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) <<= 1;', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '{val} <<= 1;'                 , ['val'])
    ]),

    # Branch on carry clear
    RuleMnemo('bcc', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if !carry;', ['addr'])]),

    # Branch on carry set
    RuleMnemo('bcs', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if carry;', ['addr'])]),

    # Branch on result zero
    RuleMnemo('beq', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if zero;', ['addr'])]),

    # Test bits in memory with accumulator
    RuleMnemo('bit', [RuleInst(r'(?P<val>.+)', 'bit({val});', ['val'])]),

    # Branch on result minus
    RuleMnemo('bmi', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if negative;', ['addr'])]),

    # Branch on result not zero
    RuleMnemo('bne', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if !zero;', ['addr'])]),

    # Branch on result plus
    RuleMnemo('bpl', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if !negative;', ['addr'])]),

    # Force break
    RuleMnemo('brk', 'irqcall(0);'),

    # Branch on overflow clear
    RuleMnemo('bvc', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if !overflow;', ['addr'])]),

    # Branch on overflow set
    RuleMnemo('bvs', [RuleInst(r'(?P<addr>.+)', 'goto {addr} if overflow;', ['addr'])]),

    # Clear carry flag
    RuleMnemo('clc', 'carry = false;'),

    # Clear decimal mode
    RuleMnemo('cld', 'decimal = false;'),

    # Clear interrupt disable status
    RuleMnemo('cli', 'nointerrupt = false;'),

    # Clear overflow flag
    RuleMnemo('clv', 'overflow = false;'),

    # Compare memory and accumulator
    RuleMnemo('cmp', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , 'cmp(a, *(*(({zp} + x) as *u16) as *u8));', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , 'cmp(a, *(*(({zp} as *u16) + y) as *u8));', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', 'cmp(a, *(({addr} + {reg}) as *u8));'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , 'cmp(a, {val});'                          , ['val' ])
    ]),

    # Compare memory and index X
    RuleMnemo('cpx', [RuleInst(r'(?P<val>.+)', 'cmp(x, {val});', ['val'])]),

    # Compare memory and index Y
    RuleMnemo('cpy', [RuleInst(r'(?P<val>.+)', 'cmp(y, {val});', ['val'])]),

    # Decrement memory by one
    RuleMnemo('dec', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', '-- *(({addr} + x) as *u8);', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '-- {val};'                 , ['val'])
    ]),

    # Decrement index X by one
    RuleMnemo('dex', '--x;'),

    # Decrement index Y by one
    RuleMnemo('dey', '--y;'),

    # XOR memory with accumulator
    RuleMnemo('eor', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , 'a ^= *(*(({zp} + x) as *u16) as *u8);', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , 'a ^= *(*(({zp} as *u16) + y) as *u8);', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', 'a ^= *(({addr} + {reg}) as *u8);'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , 'a ^= {val};'                          , ['val' ])
    ]),

    # Increment memory by one
    RuleMnemo('inc', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', '++ *(({addr} + x) as *u8);', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '++ {val};'                 , ['val' ])
    ]),

    # Increment index X by one
    RuleMnemo('inx', '++x;'),

    # Increment index Y by one
    RuleMnemo('iny', '++y;'),

    # Jump to new location
    RuleMnemo('jmp', [
        RuleInst(r'\(\s*(?P<addr>.+)\s*\)', 'goto *({addr} as *u16);', ['addr']),
        RuleInst(r'(?P<addr>.+)'          , 'goto {addr};'           , ['addr'])
    ]),

    # Jump to new location saving return address
    RuleMnemo('jsr', [(r'(?P<func>.+)', '{func}();', ['func'])]),

    # Load accumulator with memory
    RuleMnemo('lda', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , 'a = *(*(({zp} + x) as *u16) as *u8);', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , 'a = *(*(({zp} as *u16) + y) as *u8);', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', 'a = *(({addr} + {reg}) as *u8);'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , 'a = {val};'                          , ['val' ])
    ]),

    # Load index X with memory
    RuleMnemo('ldx', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Yy]', 'x = *(({addr} + y) as *u8);', ['addr']),
        RuleInst(r'(?P<val>.+)'            , 'x = {val};'                 , ['val' ])
    ]),

    # Load index Y with memory
    RuleMnemo('ldy', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', 'y = *(({addr} + x) as *u8);', ['addr']),
        RuleInst(r'(?P<val>.+)'            , 'y = {val};'                 , ['val' ])
    ]),

    # Shift right one bit (memory or accumulator)
    RuleMnemo('lsr', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) >>>= 1;', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '{val} >>>= 1;'                 , ['val' ])
    ]),

    # No operation
    RuleMnemo('nop', 'nop();'),

    # OR memory with accumulator
    RuleMnemo('ora', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , 'a |= *(*(({zp} + x) as *u16) as *u8);', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , 'a |= *(*(({zp} as *u16) + y) as *u8);', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', 'a |= *(({addr} + {reg}) as *u8);'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , 'a |= {val};'                          , ['val' ])
    ]),

    # Push accumulator on stack
    RuleMnemo('pha', 'push(a);'),

    # Push processor status on stack
    RuleMnemo('php', 'push(p);'),

    # Pull accumulator from stack
    RuleMnemo('pla', 'a = pop();'),

    # Pull processor status from stack
    RuleMnemo('plp', 'p = pop();'),

    # Rotate one bit left (memory or accumulator)
    RuleMnemo('rol', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) <<<<#= 1;', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '{val} <<<<#= 1;'                 , ['val' ])
    ]),

    # Rotate one bit right (memory or accumulator)
    RuleMnemo('ror', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) >>>>#= 1;', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '{val} >>>>#= 1;'                 , ['val' ])
    ]),

    # Return from interrupt
    RuleMnemo('rti', 'irqreturn;'),

    # Return from subroutine
    RuleMnemo('rts', 'return;'),

    # Subtract memory from accumulator with borrow
    RuleMnemo('sbc', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , 'a -#= *(*(({zp} + x) as *u16) as *u8);', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , 'a -#= *(*(({zp} as *u16) + y) as *u8);', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', 'a -#= *(({addr} + {reg}) as *u8);'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , 'a -#= {val};'                          , ['val' ])
    ]),

    # Set carry flag
    RuleMnemo('sec', 'carry = true;'),

    # Set decimal mode
    RuleMnemo('sed', 'decimal = true;'),

    # Set interrupt disable status
    RuleMnemo('sei', 'nointerrupt = true;'),

    # Store accumulator in memory
    RuleMnemo('sta', [
        RuleInst(r'\(\s*(?P<zp>.+)\s*,\s*[Xx]\s*\)'   , '*(*(({zp} + x) as *u16) as *u8) = a;', ['zp'  ]),
        RuleInst(r'\(\s*(?P<zp>.+)\s*\)\s*,\s*[Yy]'   , '*(*(({zp} as *u16) + y) as *u8) = a;', ['zp'  ]),
        RuleInst(r'(?P<addr>.+)\s*,\s*(?P<reg>[XxYy])', '*(({addr} + {reg}) as *u8) = a;'     , ['addr'], ['reg']),
        RuleInst(r'(?P<val>.+)'                       , '{val} = a;'                          , ['val' ])
    ]),

    # Store index X in memory
    RuleMnemo('stx', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Yy]', '*(({addr} + y) as *u8) = x;', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '{val} = x;'                 , ['val' ])
    ]),

    # Store index Y in memory
    RuleMnemo('sty', [
        RuleInst(r'(?P<addr>.+)\s*,\s*[Xx]', '*(({addr} + x) as *u8) = y;', ['addr']),
        RuleInst(r'(?P<val>.+)'            , '{val} = y;'                 , ['val' ])
    ]),

    # Transfer accumulator to index X
    RuleMnemo('tax', 'x = a;'),

    # Transfer accumulator to index Y
    RuleMnemo('tay', 'y = a;'),

    # Transfer stack pointer to index X
    RuleMnemo('tsx', 'x = s;'),

    # Transfer index X to accumulator
    RuleMnemo('txa', 'a = x;'),

    # Transfer index X to stack pointer
    RuleMnemo('txs', 's = x;'),

    # Transfer index Y to accumulator
    RuleMnemo('tya', 'a = y;'),
]


_INST_MOS65C02 = _INST_MOS6502 + [
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
]


_INST_ROCKWELL65C02 = _INST_MOS65C02 + [
#goto {-128..127} if *({0..255} as *u8) $ {0..7}
#goto {-128..127} if !(*({0..255} as *u8)) $ {0..7}
#^goto {0..65535} if *({0..255} as *u8) $ {0..7}
#^goto {0..65535} if !(*({0..255} as *u8)) $ {0..7}
#
#*({0..255} as *u8) $ {0..7} = false
#*({0..255} as *u8) $ {0..7} = true
]


_INST_WDC65C02 = _INST_ROCKWELL65C02 + [
#stop_until_reset()
#wait_until_interrupt()
]


_INST_HUC6280 = _INST_ROCKWELL65C02 + [
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
]


_INST_WDC65C816 = [
# TODO
]


_INST_SPC700 = _INST_MOS6502 + [
# TODO some instructions were removed from MOS6502
]
