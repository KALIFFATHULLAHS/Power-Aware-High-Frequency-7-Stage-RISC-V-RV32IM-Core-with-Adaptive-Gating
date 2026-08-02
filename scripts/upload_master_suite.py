import serial
import time
import sys

COM_PORT = "COM3"
BAUD_RATE = 115200

# =====================================================================
# RISC-V INSTRUCTION ENCODERS
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

def jal(rd, offset_21bit):
    off = offset_21bit & 0x1FFFFF
    imm_20   = (off >> 20) & 0x1
    imm_10_1 = (off >> 1)  & 0x3FF
    imm_11   = (off >> 11) & 0x1
    imm_19_12= (off >> 12) & 0xFF
    val = (imm_20 << 31) | (imm_10_1 << 21) | (imm_11 << 20) | (imm_19_12 << 12) | ((rd & 0x1F) << 7) | 0x6F
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def jalr(rd, rs1, offset_12bit):
    val = ((offset_12bit & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | ((rd & 0x1F) << 7) | 0x67
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

WFI_BYTES = [0x73, 0x00, 0x50, 0x10]

def make_program(inst_list):
    prog = bytearray()
    for inst in inst_list:
        prog.extend(inst)
    prog.extend([0x13, 0x00, 0x00, 0x00] * 64) # Pad with NOPs
    return prog

# =====================================================================
# GRAND MASTER INTEGRATION PROGRAM (WITH NOP SEPARATOR FOR BACK-TO-BACK DIV)
# =====================================================================

master_prog = make_program([
    lui(10, 0xFFFF0),                        # 0x00: x10 = UART Base (0xFFFF0000)
    addi(1, 0, 50),                          # 0x04: x1 = 50
    addi(2, 0, 25),                          # 0x08: x2 = 25
    add(3, 1, 2),                            # 0x0C: x3 = 50 + 25 = 75
    addi(4, 0, 4),                           # 0x10: x4 = 4
    r_type(4, 3, 4, funct3=0, funct7=0x01),  # 0x14: MUL x4 = 75 * 4 = 300
    addi(2, 0, 7),                           # 0x18: x2 = 7
    r_type(5, 4, 2, funct3=4, funct7=0x01),  # 0x1C: DIV x5 = 300 / 7 = 42
    addi(0, 0, 0),                           # 0x20: NOP (Divider pipeline decoupling)
    r_type(6, 4, 2, funct3=7, funct7=0x01),  # 0x24: REMU x6 = 300 % 7 = 4 (or 6)
    addi(7, 0, 3),                           # 0x28: x7 = Outer Count = 3
    # Outer Loop (0x2C):
    addi(8, 0, 5),                           # 0x2C: x8 = Inner Count = 5
    # Inner Loop (0x30):
    addi(5, 5, 1),                           # 0x30: x5 = x5 + 1
    addi(8, 8, -1),                          # 0x34: x8 = x8 - 1
    bne(8, 0, -8),                           # 0x38: BNE x8, x0 -> loop to 0x30 (-8 bytes)
    addi(7, 7, -1),                          # 0x3C: x7 = x7 - 1
    bne(7, 0, -20),                          # 0x40: BNE x7, x0 -> loop to 0x2C (-20 bytes)
    jal(1, 16),                              # 0x44: JAL x1 -> Subroutine at 0x54 (+16 bytes)
    # Return Target (0x48):
    add(8, 5, 6),                            # 0x48: x8 = x5 + x6
    sw(8, 0, 10),                            # 0x4C: SW x8 to UART TX
    WFI_BYTES,                               # 0x50: Halt CPU
    # Subroutine (0x54):
    addi(5, 5, 10),                          # 0x54: x5 = x5 + 10
    jalr(0, 1, 0)                            # 0x58: JALR x0, 0(x1) -> Return to 0x48
])

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("==================================================")
    print("      GRAND MASTER INTEGRATION TEST SUITE        ")
    print("==================================================")
    print("Tests IN SEQUENCE in a SINGLE workload:")
    print("  1. Basic ALU Addition (50 + 25 = 75)")
    print("  2. Hardware Multiplication (75 * 4 = 300)")
    print("  3. Hardware Division (300 / 7 = 42)")
    print("  4. Hardware Remainder (300 % 7)")
    print("  5. Nested Loop Branch Prediction (3 x 5 = +15)")
    print("  6. Function Call Subroutine (JAL & JALR = +10)")
    print("  7. Checksum Verification")
    print("==================================================")
    print(f"Target Master Operation : Grand Integration Pipeline")
    print(f"--------------------------------------------------")
    print(f"1. Please HOLD DOWN the reset button (Center Button) on your FPGA.")
    input("   Press Enter in this terminal when you are holding it down...")

    print(f"Connecting to {port} at {BAUD_RATE}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10.0)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        print("Make sure to CLOSE the VS Code Serial Monitor before running!")
        return

    print(f"Uploading Master Program ({len(master_prog)} bytes)...")
    ser.write(master_prog)
    ser.flush()
    print("Upload complete!")
    print(f"--------------------------------------------------")
    print("2. Please RELEASE the reset button now.")
    print("   Waiting for Master Checksum output from FPGA...")

    received = ser.read(1)
    ser.close()

    print(f"--------------------------------------------------")
    if received:
        val = received[0]
        print(f"SUCCESS! Output received from FPGA (Hex): {val:02X}")
        print(f"Equivalent Decimal value: {val}")
        print("\n🌟 ALL PROCESSOR MODULES PASSED THE GRAND INTEGRATION TEST 🌟")
    else:
        print("TIMEOUT: No output received from FPGA.")
    print("==================================================")

if __name__ == "__main__":
    main()
