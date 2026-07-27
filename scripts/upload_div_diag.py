import serial
import time
import sys

COM_PORT = "COM3"
BAUD_RATE = 115200

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

# DIV (Signed): 100 / 5 = 20 (0x14)
div_signed_prog = make_program([
    lui(10, 0xFFFF0),
    addi(1, 0, 100),
    addi(2, 0, 5),
    r_type(3, 1, 2, funct3=4, funct7=0x01), # DIV (signed)
    sw(3, 0, 10),
    WFI_BYTES
])
div_signed_prog.extend([0x13, 0x00, 0x00, 0x00] * 64)

# DIVU (Unsigned): 100 / 5 = 20 (0x14)
div_unsigned_prog = make_program([
    lui(10, 0xFFFF0),
    addi(1, 0, 100),
    addi(2, 0, 5),
    r_type(3, 1, 2, funct3=5, funct7=0x01), # DIVU (unsigned)
    sw(3, 0, 10),
    WFI_BYTES
])
div_unsigned_prog.extend([0x13, 0x00, 0x00, 0x00] * 64)

def run_test(name, prog, expected_hex, expected_dec):
    print(f"\n==================================================")
    print(f"  RUNNING TEST: {name}")
    print(f"  Expected Output: 0x{expected_hex:02X} (Decimal {expected_dec})")
    print(f"--------------------------------------------------")
    print(f"STEP 1: PRESS and HOLD the Center Reset button (M14) on your FPGA NOW.")
    input("        Keep holding it down and press ENTER here...")

    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=15.0)
    except Exception as e:
        print(f"Error opening port {COM_PORT}: {e}")
        print("Make sure to CLOSE the VS Code Serial Monitor before running!")
        return

    print(f"Uploading program ({len(prog)} bytes)... Please keep holding Reset...")
    ser.write(prog)
    ser.flush()
    time.sleep(0.2)
    print("Upload complete!")
    print(f"--------------------------------------------------")
    print("STEP 2: You can RELEASE the reset button now.")
    print("        Waiting for output from FPGA...")

    received = ser.read(1)
    ser.close()

    print("--------------------------------------------------")
    if received:
        val = received[0]
        print(f"RESULT: Output received (Hex): {val:02X}")
        print(f"RESULT: Decimal value      : {val}")
        if val == expected_hex:
            print(">>> TEST STATUS: PASSED! <<<")
        else:
            print(f">>> TEST STATUS: FAILED! Expected 0x{expected_hex:02X}, got 0x{val:02X} <<<")
    else:
        print(">>> TEST STATUS: TIMEOUT (No output received) <<<")
    print("==================================================")

def main():
    print("Select Division Mode to Test:")
    print("  [1] Signed Division DIV   (100 / 5 = 20 / 0x14)")
    print("  [2] Unsigned Division DIVU (100 / 5 = 20 / 0x14)")
    choice = input("Enter choice (1 or 2) [default=1]: ").strip() or "1"

    if choice == "2":
        run_test("Unsigned Division (DIVU)", div_unsigned_prog, 0x14, 20)
    else:
        run_test("Signed Division (DIV)", div_signed_prog, 0x14, 20)

if __name__ == "__main__":
    main()
