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
    prog.extend([0x13, 0x00, 0x00, 0x00] * 64) # Pad with NOPs
    return prog

# =====================================================================
# EDGE CASE TEST SUITE PROGRAMS
# =====================================================================

# 1. Division by Zero Edge Case: 100 / 0 = 0xFFFFFFFF (Truncated to lower byte 0xFF / 255)
def get_div_zero_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # x10 = UART Base
        addi(1, 0, 100),                         # x1 = 100
        addi(2, 0, 0),                           # x2 = 0
        r_type(3, 1, 2, funct3=4, funct7=0x01),  # DIV x3, x1, x2 (100 / 0 -> 0xFFFFFFFF)
        sw(3, 0, 10),                            # SW x3 to UART (Lower byte 0xFF / 255)
        WFI_BYTES                                # Halt
    ])

# 2. Hardware Remainder (REMU): 100 % 7 = 2 (0x02)
def get_rem_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # x10 = UART Base
        addi(1, 0, 100),                         # x1 = 100
        addi(2, 0, 7),                           # x2 = 7
        r_type(3, 1, 2, funct3=7, funct7=0x01),  # REMU x3, x1, x2 (100 % 7 = 2)
        sw(3, 0, 10),                            # SW x3 to UART (0x02)
        WFI_BYTES                                # Halt
    ])

# 3. Chained Multiply & Divide Stress: (15 * 8) / 6 = 20 (0x14)
def get_mul_div_chain_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # x10 = UART Base
        addi(1, 0, 15),                          # x1 = 15
        addi(2, 0, 8),                           # x2 = 8
        addi(4, 0, 6),                           # x4 = 6
        r_type(5, 1, 2, funct3=0, funct7=0x01),  # MUL x5 = 15 * 8 = 120
        r_type(3, 5, 4, funct3=4, funct7=0x01),  # DIV x3 = 120 / 6 = 20 (0x14)
        sw(3, 0, 10),                            # SW x3 to UART (0x14)
        WFI_BYTES                                # Halt
    ])

# 4. Fibonacci Sequence Iteration: Fib(8) = 21 (0x15)
def get_fibonacci_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # 0x00: x10 = UART Base
        addi(1, 0, 0),                           # 0x04: x1 = Fib(0) = 0
        addi(2, 0, 1),                           # 0x08: x2 = Fib(1) = 1
        addi(4, 0, 8),                           # 0x0C: x4 = Loop N = 8
        # Loop body (0x10):
        r_type(3, 1, 2, funct3=0, funct7=0x00),  # 0x10: ADD x3 = x1 + x2
        addi(1, 2, 0),                           # 0x14: x1 = x2
        addi(2, 3, 0),                           # 0x18: x2 = x3
        addi(4, 4, -1),                          # 0x1C: x4 = x4 - 1
        bne(4, 0, -16),                          # 0x20: BNE x4, x0 -> loop to 0x10 (-16 bytes)
        sw(1, 0, 10),                            # 0x24: SW x1 (Fib(8) = 21 / 0x15) to UART
        WFI_BYTES                                # 0x28: Halt
    ])

TESTS = {
    "1": {
        "name": "Division by Zero Edge Case (100 / 0)",
        "expected": "0xFF (Decimal 255)",
        "get_prog": get_div_zero_prog
    },
    "2": {
        "name": "Hardware Remainder REMU (100 % 7)",
        "expected": "0x02 (Decimal 2)",
        "get_prog": get_rem_prog
    },
    "3": {
        "name": "MUL & DIV Pipeline Chain ((15 * 8) / 6)",
        "expected": "0x14 (Decimal 20)",
        "get_prog": get_mul_div_chain_prog
    },
    "4": {
        "name": "Fibonacci Sequence Iteration (Fib(8))",
        "expected": "0x15 (Decimal 21)",
        "get_prog": get_fibonacci_prog
    }
}

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("==================================================")
    print("      COMPLEX EDGE CASE & STRESS TEST SUITE       ")
    print("==================================================")
    print("  1. Division by Zero Edge Case (100 / 0 = 0xFF)")
    print("  2. Hardware Remainder REMU (100 % 7 = 0x02)")
    print("  3. MUL & DIV Pipeline Chain ((15 * 8) / 6 = 20)")
    print("  4. Fibonacci Sequence Iteration (Fib(8) = 21)")
    print("==================================================")

    choice = input("Select Test Option (1-4): ").strip()
    if choice not in TESTS:
        print("Invalid selection! Exiting.")
        return

    test = TESTS[choice]
    prog_bytes = test["get_prog"]()

    print(f"\nSelected Test: {test['name']}")
    print(f"Expected Output: {test['expected']}")
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

    print(f"Uploading program ({len(prog_bytes)} bytes)...")
    ser.write(prog_bytes)
    ser.flush()
    print("Upload complete!")
    print(f"--------------------------------------------------")
    print("2. Please RELEASE the reset button now.")
    print("   Waiting for output from FPGA...")

    received = ser.read(1)
    ser.close()

    print(f"--------------------------------------------------")
    if received:
        val = received[0]
        print(f"SUCCESS! Output received from FPGA (Hex): {val:02X}")
        print(f"Equivalent Decimal value: {val}")
    else:
        print("TIMEOUT: No output received from FPGA.")
    print("==================================================")

if __name__ == "__main__":
    main()
