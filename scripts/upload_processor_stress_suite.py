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

def make_program(inst_list):
    prog = bytearray()
    for inst in inst_list:
        prog.extend(inst)
    prog.extend([0x13, 0x00, 0x00, 0x00] * 64) # Pad with NOPs
    return prog

# =====================================================================
# REAL PROCESSOR COMPLEX STRESS TEST SUITE
# Expected Output: Decimal 88 (Hex 0x58, Binary 0b01011000)
# =====================================================================

stress_prog = make_program([
    lui(10, 0xFFFF0),                        # 0x00: x10 = MMIO Base (0xFFFF0000)
    lui(11, 0x00001),                        # 0x04: x11 = Data RAM Base (0x00001000)
    addi(1, 0, 12),                          # 0x08: x1 = 12
    addi(2, 0, 5),                           # 0x0C: x2 = 5
    sw(1, 0, 11),                            # 0x10: RAM[0x1000] = 12 (Store Word)
    sw(2, 4, 11),                            # 0x14: RAM[0x1004] = 5  (Store Word)
    lw(3, 0, 11),                            # 0x18: x3 = RAM[0x1000] = 12 (Load-to-Use hazard test)
    lw(4, 4, 11),                            # 0x1C: x4 = RAM[0x1004] = 5
    addi(12, 0, 8),                          # 0x20: x12 = Loop Count = 8
    addi(5, 0, 0),                           # 0x24: x5 = Accumulator = 0
    # --- LOOP START (0x28) ---
    r_type(6, 3, 4, funct3=0, funct7=0x01),  # 0x28: x6 = MUL x3 * x4
    add(5, 5, 6),                            # 0x2C: x5 = Accumulator + x6
    addi(3, 3, 1),                           # 0x30: x3++
    addi(12, 12, -1),                        # 0x34: Loop Count--
    bne(12, 0, -16),                         # 0x38: BNE x12 != 0 -> Jump to 0x28
    # --- LOOP END --- Accumulator x5 = 620
    jal(1, 16),                              # 0x3C: JAL x1 -> Subroutine at 0x4C (+16 bytes)
    # --- RETURN TARGET (0x40) ---
    sw(5, 0, 10),                            # 0x40: Output x5 to UART TX (0xFFFF0000)
    sw(5, 4, 10),                            # 0x44: Output x5 to Board LEDs (0xFFFF0004)
    jal(0, 0),                               # 0x48: Halt loop
    # --- SUBROUTINE (0x4C) ---
    sw(1, 0, 11),                            # 0x4C: Save RA (x1) to RAM stack [0x1000]
    addi(7, 0, 7),                           # 0x50: x7 = 7
    r_type(5, 5, 7, funct3=4, funct7=0x01),  # 0x54: DIV x5 = 620 / 7 = 88 (0x58)
    lw(1, 0, 11),                            # 0x58: Restore RA (x1) from RAM stack [0x1000]
    jalr(0, 1, 0)                            # 0x5C: JALR -> Return to 0x40
])

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("==================================================")
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
            if val == 88 or val == 0x58:
                print("\n🌟 PROCESSOR COMPLEX STRESS TEST PASSED 🌟")
            else:
                print(f"Result Received: {val} (Expected: 88 / 0x58)")
        else:
            print("TIMEOUT: No output received from FPGA.")
        print("==================================================")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
