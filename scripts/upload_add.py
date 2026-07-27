import serial
import time
import sys

# Default port
COM_PORT = "COM3"
BAUD_RATE = 115200

# RISC-V program to add 5 + 10 = 15 (0x0F)
# Assembly:
# 0x00: lui x10, 0xFFFF0      -> FFFF0537
# 0x04: addi x1, x0, 5        -> 00500093
# 0x08: addi x2, x0, 10       -> 00A00113
# 0x0C: add x3, x1, x2        -> 002081B3 (x3 = 15)
# 0x10: sw x3, 0(x10)         -> 00352023 (Writes to UART TX)
# 0x14: wfi                   -> 73005010 (Halt CPU permanently)

program_bytes = bytearray([
    0x37, 0x05, 0xFF, 0xFF,  # LUI x10, 0xFFFF0
    0x93, 0x00, 0xC0, 0x03,  # ADDI x1, x0, 60
    0x13, 0x01, 0xA0, 0x00,  # ADDI x2, x0, 10
    0xB3, 0x81, 0x20, 0x00,  # ADD x3, x1, x2
    0x23, 0x20, 0x35, 0x00,  # SW x3, 0(x10)
    0x73, 0x00, 0x50, 0x10   # WFI (Halt CPU)
])

# Pad with 64 NOP instructions (0x00000013) to clear BRAM
program_bytes.extend([0x13, 0x00, 0x00, 0x00] * 64)

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else COM_PORT
    
    print(f"==================================================")
    print(f"1. Please HOLD DOWN the reset button (Center Button) on your FPGA.")
    input("   Press Enter in this terminal when you are holding it down...")
    
    print(f"Connecting to {port} at {BAUD_RATE}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10.0)
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        print(f"Make sure to CLOSE the VS Code Serial Monitor before running!")
        return
        
    print(f"Uploading program ({len(program_bytes)} bytes)...")
    ser.write(program_bytes)
    ser.flush()
    print(f"Upload complete!")
    print(f"--------------------------------------------------")
    print(f"2. Please RELEASE the reset button now.")
    print(f"   Waiting for outputs from the FPGA...")
    
    # Read 1 byte (blocks until FPGA outputs after reset release)
    received = ser.read(1)
    ser.close()
    
    print(f"--------------------------------------------------")
    if received:
        print(f"SUCCESS! Output received from FPGA (Hex): {' '.join(f'{b:02x}' for b in received)}")
        # Print decimal equivalents
        decimal_vals = [str(b) for b in received]
        print(f"Equivalent Decimal values: {', '.join(decimal_vals)}")
    else:
        print(f"TIMEOUT: No output received from FPGA. Please verify the bitstream is loaded.")
    print(f"==================================================")

if __name__ == "__main__":
    main()
