#!/usr/bin/env fish
# Lightweight wrapper to preprocess CA65-style assembly into a form wla-6502 can assemble.
# Usage: ./wla_build.sh builder/wizgen/tests/famistudio_wla.asm -o famistudio.o

if test (count $argv) -lt 1
    echo "Usage: $0 <input.asm> [wla-args...]"
    exit 2
end

set INPUT $argv[1]
set ARGS $argv[2..-1]

set TMP1 (mktemp)
set TMP2 (mktemp)

# Convert CA65-style preprocessor directives to C preprocessor directives so we can run cpp.
# This is a pragmatic approach: we do text substitutions, then run cpp -P to resolve conditionals.
# The substitutions are not perfect for every corner case but work for the common patterns in the file.

sed -E \
    -e 's/^\s*\.define\s+/#define /' \
    -e 's/^\s*\.if\s+/#if /' \
    -e 's/^\s*\.ifdef\s+/#ifdef /' \
    -e 's/^\s*\.ifndef\s+/#ifndef /' \
    -e 's/^\s*\.else\s*/#else/' \
    -e 's/^\s*\.endif\s*/#endif/' \
    -e 's/^\s*\.error\s+/#error /' \
    -e 's/\$([0-9A-Fa-f]+)/0x\1/g' \
    -e 's/\.string\(([^)]+)\)/\1/g' \
    -e 's/\.segment\s+\.string\(([^)]+)\)/segment \1/g' \
    -e 's/\.segment\s+([^:]+)\s*:\s*zeropage/segment \1 : zeropage/g' \
    $INPUT > $TMP1

# Run C preprocessor to evaluate conditionals. -P disables linemarkers.
cpp -P $TMP1 $TMP2
if test $status -ne 0
    echo "cpp failed"
    rm -f $TMP1 $TMP2
    exit 1
end

# Assemble with wla-6502 using the preprocessed file.
wla-6502 -o famistudio.o $ARGS $TMP2
set STATUS $status

rm -f $TMP1 $TMP2
exit $STATUS
