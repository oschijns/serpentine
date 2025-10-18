"""
    Assembly parser and converter for 6502 family processors
"""


_INST_MOS6502 = {
    'adc': 'a +#= {};'              , # Add memory to accumulator with carry
    'and': 'a &= {};'               , # AND memory with accumulator
    'asl': '{} <<= 1;'              , # Shift left one bit (memory or accumulator)
    'bcc': 'goto ({}) if !carry;'   , # Branch on carry clear
    'bcs': 'goto ({}) if carry;'    , # Branch on carry set
    'beq': 'goto ({}) if zero;'     , # Branch on result zero
    'bit': 'bit({});'               , # Test bits in memory with accumulator
    'bmi': 'goto ({}) if negative;' , # Branch on result minus
    'bne': 'goto ({}) if !zero;'    , # Branch on result not zero
    'bpl': 'goto ({}) if !negative;', # Branch on result plus
    'brk': 'irqcall(0);'            , # Force break
    'bvc': 'goto ({}) if !overflow;', # Branch on overflow clear
    'bvs': 'goto ({}) if overflow;' , # Branch on overflow set
    'clc': 'carry = false;'         , # Clear carry flag
    'cld': 'decimal = false;'       , # Clear decimal mode
    'cli': 'nointerrupt = false;'   , # Clear interrupt disable status
    'clv': 'overflow = false;'      , # Clear overflow flag
    'cmp': 'cmp(a, {});'            , # Compare memory and accumulator
    'cpx': 'cmp(x, {});'            , # Compare memory and index X
    'cpy': 'cmp(y, {});'            , # Compare memory and index Y
    'dec': '--({});'                , # Decrement memory by one
    'dex': '--x;'                   , # Decrement index X by one
    'dey': '--y;'                   , # Decrement index Y by one
    'eor': 'a ^= {};'               , # XOR memory with accumulator
    'inc': '++({});'                , # Increment memory by one
    'inx': '++x;'                   , # Increment index X by one
    'iny': '++y;'                   , # Increment index Y by one
    'jmp': 'goto ({});'             , # Jump to new location
    'jsr': '{}();'                  , # Jump to new location saving return address
    'lda': 'a = {};'                , # Load accumulator with memory
    'ldx': 'x = {};'                , # Load index X with memory
    'ldy': 'y = {};'                , # Load index Y with memory
    'lsr': '{} >>>= 1;'             , # Shift right one bit (memory or accumulator)
    'nop': 'nop();'                 , # No operation
    'ora': 'a |= {};'               , # OR memory with accumulator
    'pha': 'push(a);'               , # Push accumulator on stack
    'php': 'push(p);'               , # Push processor status on stack
    'pla': 'a = pop();'             , # Pull accumulator from stack
    'plp': 'p = pop();'             , # Pull processor status from stack
    'rol': '{} <<<<#= 1;'           , # Rotate one bit left (memory or accumulator)
    'ror': '{} >>>>#= 1;'           , # Rotate one bit right (memory or accumulator)
    'rti': 'irqreturn;'             , # Return from interrupt
    'rts': 'return;'                , # Return from subroutine
    'sbc': 'a -#= {};'              , # Subtract memory from accumulator with borrow
    'sec': 'carry = true;'          , # Set carry flag
    'sed': 'decimal = true;'        , # Set decimal mode
    'sei': 'nointerrupt = true;'    , # Set interrupt disable status
    'sta': '{} = a;'                , # Store accumulator in memory
    'stx': '{} = x;'                , # Store index X in memory
    'sty': '{} = y;'                , # Store index Y in memory
    'tax': 'x = a;'                 , # Transfer accumulator to index X
    'tay': 'y = a;'                 , # Transfer accumulator to index Y
    'tsx': 'x = s;'                 , # Transfer stack pointer to index X
    'txa': 'a = x;'                 , # Transfer index X to accumulator
    'txs': 's = x;'                 , # Transfer index X to stack pointer
    'tya': 'a = y;'                 , # Transfer index Y to accumulator
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