import serial
import time
import sys

COM_PORT = "COM3"
BAUD_RATE = 115200

# =====================================================================
# STANDARD COMPILER-COMPLIANT RISC-V RV32IM INSTRUCTION ENCODERS
# (Conforms 100% to Official RISC-V Unprivileged ISA Specification)
# =====================================================================
def lui(rd, imm_20bit):
    val = ((imm_20bit & 0xFFFFF) << 12) | ((rd & 0x1F) << 7) | 0x37
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def addi(rd, rs1, imm_12bit):
    val = ((imm_12bit & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | ((rd & 0x1F) << 7) | 0x13
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def add(rd, rs1, rs2):
    val = ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | ((rd & 0x1F) << 7) | 0x33
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def sw(rs2, offset_12bit, rs1):
    off = offset_12bit & 0xFFF
    imm_top = (off >> 5) & 0x7F
    imm_bot = off & 0x1F
    val = (imm_top << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (2 << 12) | (imm_bot << 7) | 0x23
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def r_type(rd, rs1, rs2, funct3, funct7):
    val = ((funct7 & 0x7F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | ((funct3 & 0x7) << 12) | ((rd & 0x1F) << 7) | 0x33
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def bne(rs1, rs2, offset_13bit):
    off = offset_13bit & 0x1FFF
    imm_12  = (off >> 12) & 0x1
    imm_10_5= (off >> 5)  & 0x3F
    imm_4_1 = (off >> 1)  & 0xF
    imm_11  = (off >> 11) & 0x1
    val = (imm_12 << 31) | (imm_10_5 << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (1 << 12) | (imm_4_1 << 8) | (imm_11 << 7) | 0x63
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def beq(rs1, rs2, offset_13bit):
    off = offset_13bit & 0x1FFF
    imm_12  = (off >> 12) & 0x1
    imm_10_5= (off >> 5)  & 0x3F
    imm_4_1 = (off >> 1)  & 0xF
    imm_11  = (off >> 11) & 0x1
    val = (imm_12 << 31) | (imm_10_5 << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | (imm_4_1 << 8) | (imm_11 << 7) | 0x63
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def blt(rs1, rs2, offset_13bit):
    off = offset_13bit & 0x1FFF
    imm_12  = (off >> 12) & 0x1
    imm_10_5= (off >> 5)  & 0x3F
    imm_4_1 = (off >> 1)  & 0xF
    imm_11  = (off >> 11) & 0x1
    val = (imm_12 << 31) | (imm_10_5 << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (4 << 12) | (imm_4_1 << 8) | (imm_11 << 7) | 0x63
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def jal(rd, offset_21bit):
    off = offset_21bit & 0x1FFFFF
    imm_20   = (off >> 20) & 0x1
    imm_10_1 = (off >> 1)  & 0x3FF
    imm_11   = (off >> 11) & 0x1
    imm_19_12= (off >> 12) & 0xFF
    val = (imm_20 << 31) | (imm_10_1 << 21) | (imm_11 << 20) | (imm_19_12 << 12) | ((rd & 0x1F) << 7) | 0x6F
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

WFI_BYTES = [0x73, 0x00, 0x50, 0x10]

def make_program(inst_list):
    prog = bytearray()
    for inst in inst_list:
        prog.extend(inst)
    prog.extend([0x13, 0x00, 0x00, 0x00] * 16) # Pad with 16 NOPs
    return prog

# =====================================================================
# FLOYD'S TRIANGLE PATTERN GENERATOR (N = 5)
# Target Output:
# 1
# 2 3
# 4 5 6
# 7 8 9 10
# 11 12 13 14 15
# =====================================================================

pattern_prog = make_program([
    lui(10, 0xFFFF0),                        # 0x00: x10 = MMIO Base (0xFFFF0000)
    addi(3, 0, 1),                           # 0x04: x3 = num = 1
    addi(4, 0, 1),                           # 0x08: x4 = i = 1 (row counter)
    addi(6, 0, 10),                          # 0x0C: x6 = constant 10

    # --- ROW_LOOP (0x10) ---
    addi(5, 0, 1),                           # 0x10: x5 = j = 1 (col counter)

    # --- COL_LOOP (0x14) ---
    blt(3, 6, 32),                           # 0x14: BLT x3 < 10 -> Jump to PRINT_SINGLE (0x34)
    r_type(7, 3, 6, funct3=4, funct7=0x01),  # 0x18: DIV x7 = x3 / 10
    addi(7, 7, 48),                          # 0x1C: ASCII '0' + tens
    sw(7, 0, 10),                            # 0x20: Output tens digit to UART TX
    r_type(7, 3, 6, funct3=6, funct7=0x01),  # 0x24: REM x7 = x3 % 10
    addi(7, 7, 48),                          # 0x28: ASCII '0' + units
    sw(7, 0, 10),                            # 0x2C: Output units digit to UART TX
    jal(0, 12),                              # 0x30: JAL -> Jump to PRINT_SPACE (0x3C)

    # --- PRINT_SINGLE (0x34) ---
    addi(7, 3, 48),                          # 0x34: ASCII '0' + num
    sw(7, 0, 10),                            # 0x38: Output single digit to UART TX

    # --- PRINT_SPACE (0x3C) ---
    addi(3, 3, 1),                           # 0x3C: num++
    beq(5, 4, 20),                           # 0x40: BEQ j == i -> Jump to PRINT_NEWLINE (0x54)
    addi(7, 0, 32),                          # 0x44: ASCII 32 = ' '
    sw(7, 0, 10),                            # 0x48: Output space to UART TX
    addi(5, 5, 1),                           # 0x4C: j++
    jal(0, -60),                             # 0x50: JAL -> Jump back to COL_LOOP (0x14)

    # --- PRINT_NEWLINE (0x54) ---
    addi(7, 0, 13),                          # 0x54: ASCII 13 = '\r'
    sw(7, 0, 10),                            # 0x58: Output '\r' to UART TX
    addi(7, 0, 10),                          # 0x5C: ASCII 10 = '\n'
    sw(7, 0, 10),                            # 0x60: Output '\n' to UART TX
    addi(4, 4, 1),                           # 0x64: i++
    addi(7, 0, 6),                           # 0x68: x7 = 6 (row upper limit)
    bne(4, 7, -92),                          # 0x6C: BNE i != 6 -> Jump back to ROW_LOOP (0x10)

    sw(3, 4, 10),                            # 0x70: Output final num (16) to Board LEDs
    WFI_BYTES                                # 0x74: WFI Low-Power Idle Mode Halt
])

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("=========================================================")
    print("  RISC-V RV32IM FLOYD'S TRIANGLE PATTERN GENERATOR (N=5) ")
    print("=========================================================")
    print("Target Printed Pattern:")
    print("  1")
    print("  2 3")
    print("  4 5 6")
    print("  7 8 9 10")
    print("  11 12 13 14 15")
    print("=========================================================")

    print("1. Please HOLD DOWN the reset button (Center Button) on your FPGA.")
    input("   Press Enter in this terminal when you are holding it down...")

    print(f"Connecting to {port} at {BAUD_RATE}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10.0)
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        print("Make sure to CLOSE any active Serial Monitor before running!")
        return

    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print(f"Uploading program payload ({len(pattern_prog)} bytes)...")
        ser.write(pattern_prog)
        ser.flush()
        time.sleep(0.1)
        print("Upload complete!")
        print("--------------------------------------------------")
        print("2. Please RELEASE the reset button now.")
        print("   Reading Serial Stream from RISC-V Core...")
        print("--------------------------------------------------\n")

        # Read output stream from core
        output_buffer = []
        start_time = time.time()
        while time.time() - start_time < 3.0:
            if ser.in_waiting > 0:
                char = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                sys.stdout.write(char)
                sys.stdout.flush()
                output_buffer.append(char)

        print("\n--------------------------------------------------")
        print("🌟 PATTERN GENERATION COMPLETE 🌟")
        print("==================================================")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
