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

def lw(rd, offset_12bit, rs1):
    val = ((offset_12bit & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | (2 << 12) | ((rd & 0x1F) << 7) | 0x03
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

WFI_BYTES = [0x73, 0x00, 0x50, 0x10]

def make_program(inst_list):
    prog = bytearray()
    for inst in inst_list:
        prog.extend(inst)
    prog.extend([0x13, 0x00, 0x00, 0x00] * 16) # Pad with 16 NOPs for fast upload
    return prog

# =====================================================================
# ULTIMATE PROCESSOR-LEVEL MAX-TOGGLE STRESS SUITE
# Workload:
#   1. Maximum Bus Toggling Bit Patterns: x1 = 0x55555555, x2 = 0xAAAAAAAA
#   2. ALU Maximum Toggle Rate: XOR, ADD, SUB, AND back-to-back
#   3. Data Hazards & RAW Forwarding Logic
#   4. DSP48 M-Extension Multiplier Thrashing: MUL, MULH, MULHU
#   5. BRAM Data Memory Bus Stress: SW x8 to RAM[0x1000]
#   6. Output Result to MMIO UART TX & Board LEDs
# Expected Output: Decimal 114 (Hex 0x72, Binary 0b01110010)
# =====================================================================

stress_prog = make_program([
    # 1. Initialize Base Addresses and Maximum Toggling Bit Patterns
    lui(30, 0xFFFF0),                        # 0x00: x30 = MMIO Base (0xFFFF0000)
    lui(20, 0x00001),                        # 0x04: x20 = Scratchpad Data RAM Base (0x00001000)
    lui(1, 0x55555),                         # 0x08: x1 = 0x55555000
    addi(1, 1, 0x555),                       # 0x0C: x1 = 0x55555555
    lui(2, 0xAAAAA),                         # 0x10: x2 = 0xAAAAA000
    addi(2, 2, -1366),                       # 0x14: x2 = 0xAAAAAAAA (-1366 = 0xAAA in 12-bit)
    addi(15, 0, 8),                          # 0x18: x15 = Loop Counter = 8

    # --- STRESS LOOP START (0x1C) ---
    r_type(3, 1, 2, funct3=4, funct7=0x00),  # 0x1C: XOR x3 = x1 ^ x2 (0xFFFFFFFF)
    r_type(4, 3, 1, funct3=4, funct7=0x00),  # 0x20: XOR x4 = x3 ^ x1 (0xAAAAAAAA)

    # RAW Data Hazards & Forwarding Logic
    r_type(5, 3, 4, funct3=0, funct7=0x00),  # 0x24: ADD x5 = x3 + x4
    r_type(6, 5, 1, funct3=0, funct7=0x20),  # 0x28: SUB x6 = x5 - x1
    r_type(7, 6, 2, funct3=7, funct7=0x00),  # 0x2C: AND x7 = x6 & x2

    # M-Extension Multiplier Unit (DSP48 Heavy Power Draw)
    r_type(8, 1, 2, funct3=0, funct7=0x01),  # 0x30: MUL   x8 = x1 * x2 (Lower 32-bit: 0x71C71C72)
    r_type(9, 1, 2, funct3=1, funct7=0x01),  # 0x34: MULH  x9 = x1 * x2 (Signed Upper 32-bit)
    r_type(14, 1, 2, funct3=3, funct7=0x01), # 0x38: MULHU x14 = x1 * x2 (Unsigned Upper 32-bit)

    # Memory Bus Stress (Store Word)
    sw(8, 0, 20),                            # 0x3C: SW x8, 0(x20) -> RAM[0x1000]

    # Loop Control
    addi(15, 15, -1),                        # 0x40: Loop Counter--
    bne(15, 0, -40),                         # 0x44: BNE x15 != 0 -> Jump to 0x1C

    # --- OUTPUT TARGET (0x48) ---
    sw(8, 0, 30),                            # 0x48: Output x8 (114 / 0x72) to UART TX (0xFFFF0000)
    sw(8, 4, 30),                            # 0x4C: Output x8 (114 / 0x72) to Board LEDs (0xFFFF0004)
    WFI_BYTES                                # 0x50: WFI Low-Power Idle Mode Halt
])

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("=========================================================")
    print("  ULTIMATE PROCESSOR-LEVEL MAX-TOGGLE STRESS BENCHMARK   ")
    print("=========================================================")
    print("  Tests Full Hardware Pipeline & Hardware Toggle Stress:")
    print("   1. Maximum Bus Toggling (0x55555555 vs 0xAAAAAAAA)")
    print("   2. Back-to-Back RAW Data Forwarding (XOR -> ADD -> SUB -> AND)")
    print("   3. Artix-7 DSP48 Multiplier Hammer (MUL, MULH, MULHU)")
    print("   4. BRAM Data Memory Bus Write Thrashing (SW x8 to RAM)")
    print("  Expected Output: Decimal 114 (Hex 0x72, Binary 0b01110010)")
    print("=========================================================")

    print("1. Please HOLD DOWN the reset button (Center Button) on your FPGA.")
    input("   Press Enter in this terminal when you are holding it down...")

    print(f"Connecting to {port} at {BAUD_RATE}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10.0)
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        print("Make sure to CLOSE the VS Code Serial Monitor before running!")
        return

    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print(f"Uploading program ({len(stress_prog)} bytes)...")
        ser.write(stress_prog)
        ser.flush()
        time.sleep(0.1)
        print("Upload complete!")
        print("--------------------------------------------------")
        print("2. Please RELEASE the reset button now.")
        print("   Waiting for outputs from the FPGA...")

        received = ser.read(1)
        print("--------------------------------------------------")
        if received:
            val = received[0]
            print(f"SUCCESS! Output received from FPGA (Hex): 0x{val:02X}")
            print(f"Equivalent Decimal value: {val}")
            if val == 114 or val == 0x72:
                print("\n🌟 ULTIMATE PROCESSOR STRESS TEST PASSED 🌟")
                print("Hardware Board LED Verification: LEDs 6, 5, 4, 1 MUST BE ON!")
            else:
                print(f"Result Received: {val} (Expected: 114 / 0x72)")
        else:
            print("TIMEOUT: No output received from FPGA.")
        print("==================================================")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
