# Power-Aware High-Frequency 7-Stage RISC-V RV32IM Core with Adaptive Gating

An advanced, power-optimized 32-bit RISC-V processor core designed for high-frequency operations on Xilinx 7-Series FPGAs. The core implements the RV32IM instruction set architecture with dynamic, stage-level adaptive clock gating, approximate arithmetic mode, WFI idle shutdown, and a UART-based bootloader.

---

## 🌟 Key Features

*   **7-Stage Pipeline:** Deeply pipelined architecture (IF1 → IF2 → ID → EX1 → EX2 → MEM → WB) allowing high-frequency execution.
*   **Adaptive Stage Gating (Dynamic Clock Gating):** Uses a central `stage_gating_controller` and custom Xilinx `BUFGCE` clock buffers in `clock_manager` to dynamically disable pipeline stages and arithmetic units (Multiplier, Divider) when idle, during stalls, or when disabled by power modes.
*   **Approximate Arithmetic Mode:** Features an energy-saving Approximate ALU mode that truncates the 4 LSBs of operands to reduce active power during non-critical mathematical computations.
*   **Wait For Interrupt (WFI) Idle Mode:** Shuts down all stage clocks during idle states, entering a ultra-low-power sleep mode until woken up by system triggers.
*   **Branch Prediction Unit (BPU):** Minimizes branch penalties using hardware branch prediction.
*   **Full Hazard & Forwarding Support:** Integrated hazard unit resolving Read-After-Write (RAW) and load-use dependencies with minimal stall cycles.
*   **Dual-Port BRAM & UART Program Loader:** Built-in bootloader allowing users to stream application binaries directly into instruction memory over a serial interface.
*   **Memory-Mapped I/O (MMIO):** Standardized memory accesses for UART TX communication and LED state indicators.

---

## 🏗️ Processor Architecture & Pipeline

```mermaid
graph TD
    subgraph Pipeline Stages
        IF1[1. IF1: Fetch 1] -->|PC| IF2[2. IF2: Fetch 2]
        IF2 -->|Instruction / PC| ID[3. ID: Decode & RegFile]
        ID -->|rs1, rs2, control| EX1[4. EX1: Branch Resolving]
        EX1 -->|ALU ops, operands| EX2[5. EX2: ALU / MUL / DIV]
        EX2 -->|Result| MEM[6. MEM: Load / Store]
        MEM -->|Writeback Data| WB[7. WB: Writeback]
    end

    subgraph Power & Clock Gating
        SGC[Stage Gating Controller]
        CM[Clock Manager / BUFGCE]
        CSR[CSR Unit: mpower / mapprox]
        
        CSR -->|Power Mask / Approx Enable| SGC
        SGC -->|ce_if1...ce_wb, ce_mul/div| CM
        CM -->|clk_if1...clk_wb| Pipeline_Stages
    end

    classDef stage fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:#fff;
    classDef control fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff;
    class IF1,IF2,ID,EX1,EX2,MEM,WB stage;
    class SGC,CM,CSR control;
```

### Pipeline Overview
1.  **IF1 (Instruction Fetch 1):** Generates target PC using the Branch Prediction Unit.
2.  **IF2 (Instruction Fetch 2):** Fetches the instruction byte-word from dual-port BRAM memory.
3.  **ID (Instruction Decode):** Decodes RISC-V instructions, reads registers from the Register File, and detects hazard conditions.
4.  **EX1 (Execution Stage 1):** Pre-evaluates branch targets and triggers fast branch resolution.
5.  **EX2 (Execution Stage 2):** Performs exact or approximate ALU operations, starts iterative division or runs DSP-optimized multiplication.
6.  **MEM (Memory Stage):** Conducts data memory read/write requests.
7.  **WB (Writeback Stage):** Writes results back into the Register File and handles WFI halt requests.

---

## 📂 Project Directory Structure

The project code is organized as follows:

```text
├── README.md                           # Project Documentation
├── build_and_program.tcl               # Vivado Batch Build & Program TCL Script
├── program_fpga.tcl                    # Hardware Manager FPGA Programming Script
├── ricscv.xpr                          # Vivado Project File
├── tb_riscv_core_behav.wcfg            # Testbench Waveform Configuration
├── scripts/
│   ├── upload_master_suite.py          # Grand Master Integration Test Program (ALU, MUL, DIV, REM, Loops, Subroutines)
│   ├── upload_edge_cases.py            # Edge Case Suite (Div-by-zero, REMU, MUL-DIV pipeline chain, Fib)
│   ├── upload_test_advanced.py         # Advanced Instruction Set Verification Suite
│   └── upload_div_new.py               # Standard Division Verification Script
└── ricscv.srcs/
    ├── constrs_1/new/
    │   └── risc_v.xdc                  # FPGA Constraints File (Pin Assignments)
    └── sources_1/new/
        ├── clock_manager.v             # MMCM & BUFGCE Gated Clock distribution
        ├── stage_gating_controller.v   # Dynamic clock enable logic for pipeline & execution blocks
        ├── riscv_core_top.v            # Top-level core file interconnecting all modules
        ├── riscv_core_tb.v             # Core Simulation Testbench
        ├── bram_imem.v                 # Instruction BRAM Memory (w/ UART Bootloader)
        ├── bram_dmem.v                 # Data BRAM Memory
        ├── register_file.v             # 32-register general purpose RF
        ├── csr_unit.v                  # Cycle, Instret & Custom Power/Approx CSRs
        ├── hazard_unit.v               # Hazard control (stalls, flushes, misprediction recovery)
        ├── forwarding_unit.v           # Forwarding paths to bypass data to EX1/EX2
        ├── branch_predictor.v          # Hardware BPU (BHT + BTB)
        ├── if1.v                       # Pipeline Fetch 1 Stage
        ├── if2.v                       # Pipeline Fetch 2 Stage
        ├── id.v                        # Pipeline Decode Stage
        ├── ex1.v                       # Pipeline Execute 1 Stage
        ├── ex2.v                       # Pipeline Execute 2 Stage (ALU & Execution Muxing)
        ├── mem.v                       # Pipeline Memory Access Stage
        ├── wb.v                        # Pipeline Writeback Stage
        ├── mul_unit.v                  # DSP-Optimized hardware multiplier
        ├── div_unit.v                  # Iterative 32-cycle restoring hardware divider
        ├── uart_rx.v                   # UART Receiver module (loader & debug)
        ├── uart_tx_minimal.v           # MMIO UART Transmitter
        ├── uart_rx_minimal.v           # Minimal UART Receiver
        ├── program.mem                 # Default compiled binary for BRAM simulation
        └── fpga_top.v                  # FPGA wrapper top-level
```

---

## 🧪 Hardware Testing & UART Binary Upload

Application binaries can be uploaded directly over the UART serial interface (`115200 Baud`) onto the physical FPGA board without re-synthesizing:

### 1. Grand Master Integration Test
Runs ALU addition, hardware multiplication, hardware division, hardware remainder, nested loops, and subroutine function calls in a single program:
```powershell
python scripts/upload_master_suite.py
```
- **Instructions**: Hold physical Center Reset button `M14` → Press `ENTER` → Release `M14` after upload completes.
- **Expected Result**: Output `0x47` / Decimal `71` (`0x49` / Decimal `73` depending on remainder sampling).

### 2. Edge Case Stress Test Suite
Tests division-by-zero, `REMU` remainder, `MUL`+`DIV` pipeline chaining, and Fibonacci recursion:
```powershell
python scripts/upload_edge_cases.py
```

---

## 🛠️ Simulation & Synthesis

### Simulation (Behavioral)
1. Open the project `ricscv.xpr` in Xilinx Vivado.
2. Set `riscv_core_tb.v` as the top simulation module.
3. Ensure your desired binary code (in hexadecimal format) is written to `program.mem` in the project root directory.
4. Run the behavioral simulation. The testbench handles automatic clock generation, bootloader reset release, and monitors MMIO UART outputs (`uart_tx`).

### FPGA Synthesis & Automated Build Script
The project is optimized for Xilinx 7-Series (Artix-7 XC7A100T-2FTG256C) FPGA architectures.
1. Run automated build script in Vivado batch mode:
   ```powershell
   vivado -mode batch -source build_and_program.tcl
   ```
2. Check resource utilization and timing reports (`fpga_top_utilization_routed.rpt`, `fpga_top_timing_summary_routed.rpt`) to verify high-frequency synthesis metrics and dynamic power savings.

