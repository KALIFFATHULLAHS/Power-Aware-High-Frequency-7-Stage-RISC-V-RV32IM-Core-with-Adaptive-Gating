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
# NEW DIVISION PROGRAM: 100 / 5 = 20 (Hex 0x14)
# =====================================================================
program_bytes = make_program([
    lui(10, 0xFFFF0),                        # x10 = 0xFFFF0000 (UART Base)
    addi(1, 0, 100),                          # x1 = 100
    addi(2, 0, 5),                            # x2 = 5
    r_type(3, 1, 2, funct3=4, funct7=0x01),   # DIV x3, x1, x2  (x3 = 100 / 5 = 20)
    sw(3, 0, 10),                             # SW x3, 0(x10) -> Writes 0x14 to UART
    WFI_BYTES                                 # Halt CPU
])

# Pad with 64 NOP instructions (0x00000013) to clear BRAM
program_bytes.extend([0x13, 0x00, 0x00, 0x00] * 64)

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("==================================================")
    print("      NEW DIVISION TEST: 100 / 5 = 20 (0x14)     ")
    print("==================================================")
    print(f"Target Operation: 100 / 5")
    print(f"Expected Output : 0x14 (Decimal 20)")
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
