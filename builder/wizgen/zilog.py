"""
    Assembly parser and converter for Z80 family processors
"""

_INST_COMMON = {
    'adc' : '{} +#= {};',
    'add' : '{} += {};',
    'and' : '{} &= {};',
    'bit' : 'bit({}, {});',
    'cp'  : 'cmp(a, {});',
    'dec' : '--({});',
    'di'  : 'nointerrupt = true;',
    'ei'  : 'nointerrupt = false;',
    'ex'  : 'swap({}, {});',
    'exx' : 'swap_shadow();',
    'halt': 'halt();',
    'im'  : 'interrupt_mode = {};',
    'inc' : '++({});',
    'jp'  : 'goto ({});',
    'jr'  : 'goto ({});', # handle flags !
    'ld'  : '{} = {};',
    'neg' : 'a = -a;',
    'or'  : '{} |= {};',
    'pop' : '{} = pop();',
    'push': 'push({});',

    # https://github.com/oschijns/customasm/blob/z80/std/cpu/z80.asm
    # TODO res
}

_INST_ZILOG80 = {
    'call' : 'call ({});',
    'ccf'  : 'carry = !carry;',
    'cpd'  : 'compare_decrement();',
    'cpdr' : 'compare_decrement_repeat();',
    'cpi'  : 'compare_increment();',
    'cpir' : 'compare_increment_repeat();',
    'cpl'  : 'a = ~a;',
    'daa'  : 'decimal_adjust();',
    'djnz' : 'decrement_branch_not_zero ({});',
    'in'   : '{} = io_read();',
    'ind'  : 'io_read_decrement();',
    'indr' : 'io_read_decrement_repeat();',
    'ini'  : 'io_read_increment();',
    'inir' : 'io_read_increment_repeat();',
    'ldd'  : 'load_decrement();',
    'lddr' : 'load_decrement_repeat();',
    'ldi'  : 'load_increment();',
    'ldir' : 'load_increment_repeat();',
    'mulub': 'a *= {};',
    'muluw': 'hl *= {};',
    'out'  : 'io_write({});',
    'outd' : 'io_write_decrement();',
    'otdr' : 'io_write_decrement_repeat();',
    'outi' : 'io_write_increment();',
    'otir' : 'io_write_increment_repeat();',

}

_INST_SM83 = {
# TODO
}