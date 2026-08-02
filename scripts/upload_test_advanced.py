import serial
import time
import sys

COM_PORT = "COM3"
BAUD_RATE = 115200

# =====================================================================
# RISC-V INSTRUCTION ENCODERS (Supports JAL, JALR, Branch BNE, etc.)
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

def bne(rs1, rs2, offset_13bit):
    off = offset_13bit & 0x1FFF
    b12 = (off >> 12) & 1
    b10_5 = (off >> 5) & 0x3F
    b4_1 = (off >> 1) & 0xF
    b11 = (off >> 11) & 1
    val = (b12 << 31) | (b10_5 << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (1 << 12) | (b4_1 << 8) | (b11 << 7) | 0x63
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def jal(rd, offset_21bit):
    off = offset_21bit & 0x1FFFFF
    b20 = (off >> 20) & 1
    b10_1 = (off >> 1) & 0x3FF
    b11 = (off >> 11) & 1
    b19_12 = (off >> 12) & 0xFF
    val = (b20 << 31) | (b10_1 << 21) | (b11 << 20) | (b19_12 << 12) | ((rd & 0x1F) << 7) | 0x6F
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def jalr(rd, rs1, offset_12bit):
    val = ((offset_12bit & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | ((rd & 0x1F) << 7) | 0x67
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

WFI_BYTES = [0x73, 0x00, 0x50, 0x10]

def make_program(inst_list):
    prog = bytearray()
    for inst in inst_list:
        prog.extend(inst)
    return prog

# =====================================================================
# ADVANCED RISC-V PROGRAMS
# =====================================================================

# 1. Loop Sum (1 + 2 + 3 + 4 + 5 = 15 / 0x0F)
def get_loop_sum_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # 0x00: x10 = UART Base
        addi(1, 0, 5),                           # 0x04: x1 = N = 5
        addi(2, 0, 0),                           # 0x08: x2 = sum = 0
        # LOOP (0x0C):
        r_type(2, 2, 1, funct3=0, funct7=0x00),  # 0x0C: sum = sum + N
        addi(1, 1, -1),                          # 0x10: N = N - 1
        bne(1, 0, -8),                           # 0x14: if N != 0 goto LOOP (offset -8)
        sw(2, 0, 10),                            # 0x18: SW sum (15 / 0x0F) to UART
        WFI_BYTES                                # 0x1C: Halt
    ])

# 2. Factorial Loop (5! = 5 * 4 * 3 * 2 * 1 = 120 / 0x78)
def get_factorial_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # 0x00: x10 = UART Base
        addi(1, 0, 5),                           # 0x04: x1 = N = 5
        addi(2, 0, 1),                           # 0x08: x2 = fact = 1
        # LOOP (0x0C):
        r_type(2, 2, 1, funct3=0, funct7=0x01),  # 0x0C: MUL fact = fact * N
        addi(1, 1, -1),                          # 0x10: N = N - 1
        bne(1, 0, -8),                           # 0x14: if N != 0 goto LOOP
        sw(2, 0, 10),                            # 0x18: SW fact (120 / 0x78) to UART
        WFI_BYTES                                # 0x1C: Halt
    ])

# 3. Function Call (JAL & JALR Function Return)
def get_func_call_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # 0x00: x10 = UART Base
        jal(1, 12),                              # 0x04: JAL x1, FUNC (offset +12 bytes to 0x10)
        sw(3, 0, 10),                            # 0x08: SW x3 (24 / 0x18) to UART
        WFI_BYTES,                               # 0x0C: Halt
        # FUNC (0x10):
        addi(4, 0, 4),                           # 0x10: x4 = 4
        addi(5, 0, 6),                           # 0x14: x5 = 6
        r_type(3, 4, 5, funct3=0, funct7=0x01),  # 0x18: MUL x3 = 4 * 6 = 24 (0x18)
        jalr(0, 1, 0)                            # 0x1C: JALR x0, 0(x1) (Return to caller)
    ])

# 4. Hardware Division (100 / 7 = 14 / 0x0E)
def get_div_prog():
    return make_program([
        lui(10, 0xFFFF0),                        # 0x00: x10 = UART Base
        addi(1, 0, 100),                         # 0x04: x1 = 100
        addi(2, 0, 7),                           # 0x08: x2 = 7
        r_type(3, 1, 2, funct3=4, funct7=0x01),  # 0x0C: DIV x3 = 100 / 7 = 14 (0x0E)
        sw(3, 0, 10),                            # 0x10: SW x3 (14 / 0x0E) to UART
        WFI_BYTES                                # 0x14: Halt
    ])

TESTS = {
    "1": {
        "name": "Loop Sum (1+2+3+4+5 = 15 / 0x0F)",
        "expected": "0x0F (Decimal 15)",
        "get_prog": get_loop_sum_prog
    },
    "2": {
        "name": "Factorial Loop (5! = 120 / 0x78)",
        "expected": "0x78 (Decimal 120)",
        "get_prog": get_factorial_prog
    },
    "3": {
        "name": "Function Call (JAL & JALR return)",
        "expected": "0x18 (Decimal 24)",
        "get_prog": get_func_call_prog
    },
    "4": {
        "name": "Hardware Division (100 / 7 = 14 / 0x0E)",
        "expected": "0x0E (Decimal 14)",
        "get_prog": get_div_prog
    }
}

def main():
    print("==================================================")
    print("     ADVANCED RISC-V LOOPS & FUNCTION TESTER     ")
    print("==================================================")
    for k, v in TESTS.items():
        print(f"  [{k}] {v['name']}")
    print("==================================================")
    
    choice = input("Enter choice (1-4) [default=1]: ").strip() or "1"
    if choice not in TESTS:
        print("Invalid choice!")
        return

    test = TESTS[choice]
    program_bytes = test["get_prog"]()
    # Always append 256 NOP bytes to overwrite any old memory in BRAM
    nop_bytes = [0x13, 0x00, 0x00, 0x00] * 64
    program_bytes.extend(nop_bytes)

    port = COM_PORT
    print(f"\nTarget Test: {test['name']}")
    print(f"Expected Output: {test['expected']}")
    print(f"Program Size: {len(program_bytes)} bytes")
    print(f"--------------------------------------------------")
    
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10.0)
    except Exception as e:
        print(f"Error opening serial port {port}: {e}")
        print("Make sure to CLOSE the VS Code Serial Monitor before running!")
        return

    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print(f"STEP 1: PRESS and HOLD the Center Reset button (M14) on your FPGA NOW.")
        input("        Keep holding it down and press ENTER here...")

        print(f"Uploading program ({len(program_bytes)} bytes)... Please keep holding Reset...")
        ser.write(program_bytes)
        ser.flush()
        time.sleep(0.1)
        print("Upload complete!")
        print(f"--------------------------------------------------")
        print("STEP 2: You can RELEASE the reset button now.")
        print("        Waiting for output from FPGA...")

        received = ser.read(1)
        print(f"--------------------------------------------------")
        if received:
            val = received[0]
            print(f"SUCCESS! Output received from FPGA (Hex): {val:02X}")
            print(f"Equivalent Decimal value: {val}")
        else:
            print("TIMEOUT: No output received from FPGA within 10 seconds.")
        print("==================================================")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
