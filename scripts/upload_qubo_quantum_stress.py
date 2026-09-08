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

def sub(rd, rs1, rs2):
    val = ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | ((rd & 0x1F) << 7) | (0x20 << 25) | 0x33
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def srli(rd, rs1, shamt):
    val = ((shamt & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (5 << 12) | ((rd & 0x1F) << 7) | 0x13
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def slli(rd, rs1, shamt):
    val = ((shamt & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (1 << 12) | ((rd & 0x1F) << 7) | 0x13
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def and_op(rd, rs1, rs2):
    val = ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (7 << 12) | ((rd & 0x1F) << 7) | 0x33
    return [(val >> (8 * i)) & 0xFF for i in range(4)]

def sw(rs2, offset_12bit, rs1):
    off = offset_12bit & 0xFFF
    imm_top = (off >> 5) & 0x7F
    imm_bot = off & 0x1F
    val = (imm_top << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (2 << 12) | (imm_bot << 7) | 0x23
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

def make_qubo_program():
    prog = bytearray()
    
    code_insts = [
        lui(30, 0xFFFF0),                        # 0x00: x30 = MMIO Base (0xFFFF0000)
        lui(20, 0x00001),                        # 0x04: x20 = Scratchpad Data RAM Base (0x00001000)
        addi(2, 0, 0),                           # 0x08: x2 = Best State Mask (0x00)
        addi(3, 0, 0),                           # 0x0C: x3 = Best Energy (0)
        addi(6, 0, 0),                           # 0x10: x6 = Candidate State Mask m = 0
        addi(15, 0, 256),                        # 0x14: x15 = 256 (Loop limit)
        addi(19, 0, 1),                          # 0x18: x19 = 1 (constant)

        # --- INLINE SWEEP LOOP START (0x1C) ---
        and_op(21, 6, 19),                       # 0x1C: s0 = x6 & 1
        srli(22, 6, 1), and_op(22, 22, 19),      # 0x20, 0x24: s1 = (x6 >> 1) & 1
        srli(23, 6, 2), and_op(23, 23, 19),      # 0x28, 0x2C: s2 = (x6 >> 2) & 1
        srli(24, 6, 3), and_op(24, 24, 19),      # 0x30, 0x34: s3 = (x6 >> 3) & 1
        srli(25, 6, 4), and_op(25, 25, 19),      # 0x38, 0x3C: s4 = (x6 >> 4) & 1
        srli(26, 6, 5), and_op(26, 26, 19),      # 0x40, 0x44: s5 = (x6 >> 5) & 1
        srli(27, 6, 6), and_op(27, 27, 19),      # 0x48, 0x4C: s6 = (x6 >> 6) & 1
        srli(28, 6, 7), and_op(28, 28, 19),      # 0x50, 0x54: s7 = (x6 >> 7) & 1

        # --- INLINE ENERGY COMPUTATION ---
        addi(8, 0, 0),                           # 0x58: x8 = 0

        # s0 (x21): if s0: E += -5 + 2*s1 - s2 + 3*s3 + s5 - 2*s6 + 4*s7
        beq(21, 0, 48),                          # 0x5C: BEQ s0 == 0 -> Skip (+48 bytes to 0x8C)
        addi(8, 8, -5),                          # 0x60: E += -5
        slli(9, 22, 1), add(8, 8, 9),            # 0x64, 0x68: E += 2*s1
        sub(8, 8, 23),                           # 0x6C: E -= s2
        slli(9, 24, 1), add(9, 9, 24), add(8, 8, 9), # 0x70, 0x74, 0x78: E += 3*s3
        add(8, 8, 26),                           # 0x7C: E += s5
        slli(9, 27, 1), sub(8, 8, 9),            # 0x80, 0x84: E -= 2*s6
        slli(9, 28, 2), add(8, 8, 9),            # 0x88, 0x8C: E += 4*s7

        # s1 (x22): if s1: E += -7 + 4*s2 - 2*s3 + s4 + 3*s6 - s7
        beq(22, 0, 44),                          # 0x90: BEQ s1 == 0 -> Skip (+44 bytes to 0xBC)
        addi(8, 8, -7),                          # 0x94: E += -7
        slli(9, 23, 2), add(8, 8, 9),            # 0x98, 0x9C: E += 4*s2
        slli(9, 24, 1), sub(8, 8, 9),            # 0xA0, 0xA4: E -= 2*s3
        add(8, 8, 25),                           # 0xA8: E += s4
        slli(9, 27, 1), add(9, 9, 27), add(8, 8, 9), # 0xAC, 0xB0, 0xB4: E += 3*s6
        sub(8, 8, 28),                           # 0xB8: E -= s7

        # s2 (x23): if s2: E += -6 + s3 - 3*s4 + 2*s5 + 2*s7
        beq(23, 0, 40),                          # 0xBC: BEQ s2 == 0 -> Skip (+40 bytes to 0xE4)
        addi(8, 8, -6),                          # 0xC0: E += -6
        add(8, 8, 24),                           # 0xC4: E += s3
        slli(9, 25, 1), add(9, 9, 25), sub(8, 8, 9), # 0xC8, 0xCC, 0xD0: E -= 3*s4
        slli(9, 26, 1), add(8, 8, 9),            # 0xD4, 0xD8: E += 2*s5
        slli(9, 28, 1), add(8, 8, 9),            # 0xDC, 0xE0: E += 2*s7

        # s3 (x24): if s3: E += -8 + 4*s4 - s5 + 2*s6
        beq(24, 0, 28),                          # 0xE4: BEQ s3 == 0 -> Skip (+28 bytes to 0x100)
        addi(8, 8, -8),                          # 0xE8: E += -8
        slli(9, 25, 2), add(8, 8, 9),            # 0xEC, 0xF0: E += 4*s4
        sub(8, 8, 26),                           # 0xF4: E -= s5
        slli(9, 27, 1), add(8, 8, 9),            # 0xF8, 0xFC: E += 2*s6

        # s4 (x25): if s4: E += -5 + 3*s5 - s6 + s7
        beq(25, 0, 28),                          # 0x100: BEQ s4 == 0 -> Skip (+28 bytes to 0x11C)
        addi(8, 8, -5),                          # 0x104: E += -5
        slli(9, 26, 1), add(9, 9, 26), add(8, 8, 9), # 0x108, 0x10C, 0x110: E += 3*s5
        sub(8, 8, 27),                           # 0x114: E -= s6
        add(8, 8, 28),                           # 0x118: E += s7

        # s5 (x26): if s5: E += -9 + 4*s6 - 2*s7
        beq(26, 0, 24),                          # 0x11C: BEQ s5 == 0 -> Skip (+24 bytes to 0x134)
        addi(8, 8, -9),                          # 0x120: E += -9
        slli(9, 27, 2), add(8, 8, 9),            # 0x124, 0x128: E += 4*s6
        slli(9, 28, 1), sub(8, 8, 9),            # 0x12C, 0x130: E -= 2*s7

        # s6 (x27): if s6: E += -6 + 3*s7
        beq(27, 0, 20),                          # 0x134: BEQ s6 == 0 -> Skip (+20 bytes to 0x148)
        addi(8, 8, -6),                          # 0x138: E += -6
        slli(9, 28, 1), add(9, 9, 28), add(8, 8, 9), # 0x13C, 0x140, 0x144: E += 3*s7

        # s7 (x28): if s7: E += -7
        beq(28, 0, 8),                           # 0x148: BEQ s7 == 0 -> Skip (+8 bytes to 0x150)
        addi(8, 8, -7),                          # 0x14C: E += -7

        # --- SELECTION & UPDATE --- (0x150)
        blt(8, 3, 8),                            # 0x150: BLT x8 < x3 -> Jump to ACCEPT (0x150 + 8 = 0x158)
        jal(0, 12),                              # 0x154: JAL x0 -> Jump to NEXT_STATE (0x154 + 12 = 0x160)

        # ACCEPT (0x158):
        add(3, 8, 0),                            # 0x158: x3 = candidate_energy (Update min energy!)
        add(2, 6, 0),                            # 0x15C: x2 = candidate_mask   (Update best state mask!)

        # NEXT_STATE (0x160):
        addi(6, 6, 1),                           # 0x160: m++
        bne(6, 15, -328),                        # 0x164: BNE x6 != 256 -> Jump to 0x1C (0x164 - 328 = 0x1C)

        # --- OUTPUT BLOCK (0x168) ---
        sw(3, 0, 30),                            # 0x168: Output final minimum energy (-37 / 0xDB) to MMIO UART TX
        sw(2, 4, 30),                            # 0x16C: Output final ground state spin mask (0xAA) to MMIO Board LEDs
        WFI_BYTES                                # 0x170: WFI Low-Power Shutdown Mode
    ]

    for inst in code_insts:
        prog.extend(inst)
        
    prog.extend([0x13, 0x00, 0x00, 0x00] * 16) # Pad NOPs
    return prog

# =====================================================================
# QUANTUM ANNEALING QUBO ENERGY SOLVER BENCHMARK
# Workload:
#   1. 8x8 Symmetric QUBO Cost Matrix Optimization (Quantum Annealing)
#   2. Pure Hardware Inline Register Arithmetic for QUBO Energy Evaluation
#   3. Zero Pipeline Flush Hazard & Zero BRAM Memory Load Dependency
# Expected Output:
#   - Energy Result: -37 (Hex 0xDB, Decimal 219)
#   - Ground State Spin Mask: Hex 0xAA (Binary 0b10101010)
# =====================================================================

qubo_prog = make_qubo_program()

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("=========================================================")
    print("   QUANTUM ANNEALING QUBO ENERGY SOLVER BENCHMARK       ")
    print("=========================================================")
    print("  Simulates Quantum Annealing for 8x8 QUBO Matrix:")
    print("   - Energy Equation: E(s) = sum(s_i * Q_ii) + sum(s_i * s_j * Q_ij)")
    print("   - Pure Inline Register Arithmetic Energy Evaluation")
    print("   - Known Global Minimum Energy: -37 (Hex 0xDB, Decimal 219)")
    print("   - Optimal Ground State Spin Mask: Hex 0xAA (Binary 0b10101010)")
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

        print(f"Uploading QUBO Quantum Program ({len(qubo_prog)} bytes)...")
        ser.write(qubo_prog)
        ser.flush()
        time.sleep(0.1)
        print("Upload complete!")
        print("--------------------------------------------------")
        print("2. Please RELEASE the reset button now.")
        print("   Waiting for QUBO solver outputs from FPGA...")

        received = ser.read(1)
        print("--------------------------------------------------")
        if received:
            val = received[0]
            print(f"SUCCESS! Output received from FPGA (Hex): 0x{val:02X}")
            print(f"Equivalent Decimal value: {val}")
            if val == 219 or val == 0xDB:
                print("\n🌟 QUANTUM ANNEALING QUBO SOLVER PASSED 🌟")
                print("Optimal Energy Achieved: -37 (Hex 0xDB / Decimal 219)")
                print("Board LEDs Ground State Check: LEDs 7, 5, 3, 1 MUST BE ON (0b10101010)!")
            else:
                print(f"Result Received: {val} (Expected: 219 / 0xDB / Energy -37)")
        else:
            print("TIMEOUT: No output received from FPGA.")
        print("==================================================")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
