; ------------------------------------------------------------
; module.asm — wrapper to make module.bin + module.sym
;                linkable with wlalink
; ------------------------------------------------------------

; === Memory map (simple 64 KB flat ROM) ===
.MEMORYMAP
    DEFAULTSLOT 0
    SLOTSIZE $10000   ; 64 KB
    SLOT 0 $0000
.ENDME

.ROMBANKSIZE $10000
.ROMBANKS 1           ; single bank

.BANK 0 SLOT 0
.ORG 0

; === Include the raw binary exactly as-is ===
INCBIN "module.bin"


; === Symbol definitions from module.sym ===
; Each one is an absolute address inside BANK 0

b0          = $0000
b1          = $0001
b2          = $0002
b3          = $0003
b4          = $0004
b5          = $0005
b6          = $0006
b7          = $0007

draw        = $8085
message     = $80A6
palette     = $80B3
scanline    = $809B

__const4    = $FFFA

__continue1 = $8018
__continue2 = $8012
__continue3 = $8034
__continue4 = $8031
__continue5 = $804C

__endloop1  = $801C
__endloop2  = $8017
__endloop3  = $8036
__endloop4  = $8033
__endloop5  = $8050
__endloop6  = $806B
__endloop7  = $8084

__loop3     = $802B
__loop4     = $802D
__loop5     = $8045
__loop6     = $805F
__loop7     = $8081
