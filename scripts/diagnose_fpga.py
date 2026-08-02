import serial
import time
import sys

COM_PORT = "COM3"
BAUD_RATE = 115200

# Diagnostic RISC-V program:
# Outputs pattern 0b10101010 (Hex 0xAA / Decimal 170) to BOTH:
# 1. UART TX at 0xFFFF0000
# 2. On-Board FPGA LEDs at 0xFFFF0004

diag_prog = bytearray([
    0x37, 0x05, 0xFF, 0xFF,  # LUI x10, 0xFFFF0 (x10 = 0xFFFF0000)
    0x93, 0x00, 0xA0, 0xAA,  # ADDI x1, x0, 170 (0xAA = 0b10101010)
    0x23, 0x20, 0x15, 0x00,  # SW x1, 0(x10) -> Send 0xAA over UART
    0x23, 0x22, 0x15, 0x00,  # SW x1, 4(x10) -> Output 0xAA to FPGA Board LEDs
    0x73, 0x00, 0x50, 0x10   # WFI (Halt CPU)
])

# Pad with NOPs (0x00000013)
diag_prog.extend([0x13, 0x00, 0x00, 0x00] * 32)

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    print("=========================================================")
    print("      RISC-V FPGA HARDWARE & BITSTREAM DIAGNOSTIC        ")
    print("=========================================================")
    print("This script checks if:")
    print("  1. The Bitstream is programmed into the Artix-7 FPGA")
    print("  2. The BRAM UART Bootloader is receiving code")
    print("  3. The Processor Core is executing instructions")
    print("  4. Hardware LEDs (0xFFFF0004) & UART TX (0xFFFF0000) work")
    print("=========================================================")

    print(f"\nConnecting to {port} at {BAUD_RATE}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=5.0)
    except Exception as e:
        print(f"ERROR opening port {port}: {e}")
        print("-> Make sure VS Code Serial Monitor or Putty is CLOSED.")
        return

    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print("\n---------------------------------------------------------")
        print("[ACTION 1] PRESS and HOLD the Reset button (M14) on your FPGA.")
        input("           While holding M14, press ENTER in this terminal...")

        print(f"\n[SENDING] Uploading {len(diag_prog)} diagnostic bytes to FPGA...")
        ser.write(diag_prog)
        ser.flush()
        time.sleep(0.1)
        print("[SENDING] Upload complete!")

        print("\n---------------------------------------------------------")
        print("[ACTION 2] RELEASE the Reset button (M14) NOW.")
        input("           After releasing M14, press ENTER to check response...")

        print("\n[CHECKING 1] Reading UART port...")
        received = ser.read(1)

        print("=========================================================")
        if received:
            val = received[0]
            print(f"✅ SUCCESS! UART Received Byte: 0x{val:02X} (Decimal: {val})")
            if val == 170 or val == 0xAA:
                print("   UART Communication & RISC-V CPU Execution ARE 100% WORKING!")
        else:
            print("❌ UART Timeout (0 bytes received over serial).")

        print("\n[CHECKING 2] LOOK AT THE 8 PHYSICAL LEDs ON YOUR FPGA BOARD:")
        print("   Expected LED Pattern for 0xAA (Decimal 170):")
        print("   [ LED7: ON | LED6: OFF | LED5: ON | LED4: OFF | LED3: ON | LED2: OFF | LED1: ON | LED0: OFF ]")
        print("---------------------------------------------------------")
        print("Q: Are LEDs 7, 5, 3, 1 ON on your FPGA board?")
        print("   - YES: The CPU & Bitstream are WORKING! (Serial RX driver issue on PC)")
        print("   - NO:  The Bitstream is NOT loaded into the FPGA via Vivado Hardware Manager.")
        print("=========================================================")

        ser.close()
    except Exception as e:
        print(f"Serial Error: {e}")

if __name__ == "__main__":
    main()
