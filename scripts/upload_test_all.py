import serial
import time
import sys

COM_PORT = "COM3"
BAUD_RATE = 115200

# =====================================================================
# RISC-V INSTRUCTION ENCODERS (Ensures 100% Correct Encoding)
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

def r_type(rd, rs1, rs2, funct3, funct7):
    val = ((funct7 & 0x7F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | ((funct3 & 0x7) << 12) | ((rd & 0x1F) << 7) | 0x33
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

WFI_BYTES = [0x73, 0x00, 0x50, 0x10]

def make_program(inst_list):
    prog = bytearray()
    for inst in inst_list:
        prog.extend(inst)
    return prog

# =====================================================================
# TEST SUITE DEFINITIONS
# =====================================================================
TESTS = {
    "1": {
        "name": "Subtraction (SUB 50 - 20 = 30 / 0x1E)",
        "expected": "0x1E (Decimal 30)",
        "bytes": make_program([
            lui(10, 0xFFFF0),
            addi(1, 0, 50),
            addi(2, 0, 20),
            r_type(3, 1, 2, funct3=0, funct7=0x20), # SUB
            sw(3, 0, 10),
            WFI_BYTES
        ])
    },
    "2": {
        "name": "Bitwise AND (AND 0x3F & 0x0F = 15 / 0x0F)",
        "expected": "0x0F (Decimal 15)",
        "bytes": make_program([
            lui(10, 0xFFFF0),
            addi(1, 0, 0x3F),
            addi(2, 0, 0x0F),
            r_type(3, 1, 2, funct3=7, funct7=0x00), # AND
            sw(3, 0, 10),
            WFI_BYTES
        ])
    },
    "3": {
        "name": "Bitwise OR (OR 0x10 | 0x05 = 21 / 0x15)",
        "expected": "0x15 (Decimal 21)",
        "bytes": make_program([
            lui(10, 0xFFFF0),
            addi(1, 0, 0x10),
            addi(2, 0, 0x05),
            r_type(3, 1, 2, funct3=6, funct7=0x00), # OR
            sw(3, 0, 10),
            WFI_BYTES
        ])
    },
    "4": {
        "name": "Bitwise XOR (XOR 0x55 ^ 0x0F = 90 / 0x5A)",
        "expected": "0x5A (Decimal 90)",
        "bytes": make_program([
            lui(10, 0xFFFF0),
            addi(1, 0, 0x55),
            addi(2, 0, 0x0F),
            r_type(3, 1, 2, funct3=4, funct7=0x00), # XOR
            sw(3, 0, 10),
            WFI_BYTES
        ])
    },
    "5": {
        "name": "Shift Left Logical (SLL 3 << 3 = 24 / 0x18)",
        "expected": "0x18 (Decimal 24)",
        "bytes": make_program([
            lui(10, 0xFFFF0),
            addi(1, 0, 3),
            addi(2, 0, 3),
            r_type(3, 1, 2, funct3=1, funct7=0x00), # SLL
            sw(3, 0, 10),
            WFI_BYTES
        ])
    },
    "6": {
        "name": "Multiplication (MUL 8 * 9 = 72 / 0x48)",
        "expected": "0x48 (Decimal 72)",
        "bytes": make_program([
            lui(10, 0xFFFF0),
            addi(1, 0, 8),
            addi(2, 0, 9),
            r_type(3, 1, 2, funct3=0, funct7=0x01), # MUL
            sw(3, 0, 10),
            WFI_BYTES
        ])
    },
    "7": {
        "name": "Set Less Than (SLT 10 < 20 = 1 / 0x01)",
        "expected": "0x01 (Decimal 1)",
        "bytes": make_program([
            lui(10, 0xFFFF0),
            addi(1, 0, 10),
            addi(2, 0, 20),
            r_type(3, 1, 2, funct3=2, funct7=0x00), # SLT
            sw(3, 0, 10),
            WFI_BYTES
        ])
    }
}

def main():
    print("==================================================")
    print("      RISC-V PROCESSOR INSTRUCTION TESTER        ")
    print("==================================================")
    print("Select a test to run:")
    for k, v in TESTS.items():
        print(f"  [{k}] {v['name']}")
    print("==================================================")
    
    choice = input("Enter choice (1-7) [default=1]: ").strip() or "1"
    if choice not in TESTS:
        print("Invalid choice!")
        return

    test = TESTS[choice]
    program_bytes = test["bytes"]
    # Pad with 64 NOPs (0x00000013) to clear BRAM
    program_bytes.extend([0x13, 0x00, 0x00, 0x00] * 64)

    port = COM_PORT
    print(f"\nTarget Test: {test['name']}")
    print(f"Expected Output: {test['expected']}")
    print(f"--------------------------------------------------")
    print(f"1. Please HOLD DOWN the reset button (Center Button) on your FPGA.")
    input("   Press Enter in this terminal when you are holding it down...")

    print(f"Connecting to {port} at {BAUD_RATE}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10.0)
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        print("Make sure to CLOSE the VS Code Serial Monitor before running!")
        return

    print(f"Uploading program ({len(program_bytes)} bytes)...")
    ser.write(program_bytes)
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
        print("TIMEOUT: No output received from FPGA. Verify bitstream & reset button.")
    print("==================================================")

if __name__ == "__main__":
    main()
