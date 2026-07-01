`timescale 1ns/1ps

//=============================================================
//  RISC-V 7-Stage RV32IM Processor Top-Level
//  Power-Gated + Approximate Arithmetic + WFI Idle + UART Loader
//  PART 1 / 4
//=============================================================

module riscv_core_top (
    input  wire        clk_in,
    input  wire        reset,

    input  wire        uart_rx,
    output wire        uart_tx,

    output wire       dbg_wfi_active,
    output reg [7:0]  dbg_led        // NEW: connect to board LEDs
);

//=============================================================
// CLOCK MANAGER + GATED CLOCKS
//=============================================================

wire ce_if1, ce_if2, ce_id, ce_ex1, ce_ex2, ce_mem, ce_wb;
wire ce_mul, ce_div, ce_approx, ce_uart, ce_csr;

wire clk_sys;
wire clk_if1, clk_if2, clk_id, clk_ex1, clk_ex2, clk_mem, clk_wb;
wire clk_mul, clk_div, clk_approx, clk_uart, clk_csr;

clock_manager clk_mgr (
    .clk_in(clk_in),
    .reset(reset),

    .ce_if1(ce_if1), .ce_if2(ce_if2), .ce_id(ce_id),
    .ce_ex1(ce_ex1), .ce_ex2(ce_ex2),
    .ce_mem(ce_mem), .ce_wb(ce_wb),

    .ce_mul(ce_mul), .ce_div(ce_div), .ce_approx(ce_approx),
    .ce_uart(ce_uart), .ce_csr(ce_csr),

    .clk_sys(clk_sys),
    .clk_if1(clk_if1), .clk_if2(clk_if2), .clk_id(clk_id),
    .clk_ex1(clk_ex1), .clk_ex2(clk_ex2),
    .clk_mem(clk_mem), .clk_wb(clk_wb),
    .clk_mul(clk_mul), .clk_div(clk_div), .clk_approx(clk_approx),
    .clk_uart(clk_uart), .clk_csr(clk_csr)
);

//=============================================================
// PIPELINE WIRES DECLARATION
//=============================================================

//---------- HAZARD / STALL / FLUSH ----------
wire stall_if, stall_id, stall_ex1, stall_ex2;
wire flush_id, flush_ex1;
wire mul_busy, div_busy;

//---------- IF1 → IF2 ----------
wire [31:0] if1_pc;
wire        if1_valid;
wire [31:0] imem_rdata;

//---------- IF2 → ID ----------
wire [31:0] id_pc;
wire [31:0] id_instr;
wire        id_valid;

//---------- ID → EX1 ----------
wire [31:0] ex1_pc;
wire [31:0] ex1_imm;
wire [31:0] ex1_instr;
wire [4:0]  ex1_rd;
wire [23:0] ex1_ctrl_bus;
wire        ex1_valid;

//---------- EX1 → EX2 ----------
wire [31:0] ex2_pc;
wire [31:0] ex2_op_a;
wire [31:0] ex2_op_b;
wire [31:0] ex2_imm;
wire [31:0] ex2_instr;
wire [4:0]  ex2_rd;
wire [23:0] ex2_ctrl_bus;
wire        ex2_valid;

//---------- EX2 → MEM ----------
wire [31:0] mem_result;
wire [31:0] mem_pc;
wire [4:0]  mem_rd;
wire [23:0] mem_ctrl_bus;
wire        mem_valid;
wire [31:0] ex2_store_data;
//---------- MEM → WB ----------
wire [31:0] wb_data;
wire [31:0] wb_pc;
wire [23:0] wb_ctrl_bus;
wire [4:0]  wb_rd;
wire        wb_valid;
wire [31:0] mem_instr;
wire [31:0] wb_instr;
//=============================================================
// INSTRUCTION MEMORY (IMEM) + UART LOADER
//=============================================================
// You may use Xilinx BRAM IP or handwritten BRAM module.

wire [31:0] imem_addr = if1_pc;

bram_imem imem (
    .clk(clk_sys),
    .addr(imem_addr[15:2]),
    .rdata(imem_rdata),
    .uart_clk(clk_uart),
    .uart_rx(uart_rx),
    .uart_tx(uart_tx)
);

//=============================================================
// DATA MEMORY (DMEM)
//=============================================================
//=============================================================
// DATA MEMORY (DMEM)
//=============================================================

wire [31:0] dmem_addr;
wire [31:0] dmem_wdata;
wire [3:0]  dmem_wstrb;
wire [31:0] dmem_rdata;

// ---------------------------------------------------------------------
// MMIO:
//  0xFFFF0000 -> UART TX (byte)
//  0xFFFF0004 -> LED GPIO (lower 8 bits)
// ---------------------------------------------------------------------
localparam UART_ADDR = 32'hFFFF_0000;
localparam LED_ADDR  = 32'hFFFF_0004;

wire dmem_we_raw  = (dmem_wstrb != 4'b0000);
wire dmem_is_uart = dmem_we_raw && (dmem_addr == UART_ADDR);
wire dmem_is_led  = dmem_we_raw && (dmem_addr == LED_ADDR);
wire dmem_we_real = dmem_we_raw && !dmem_is_uart && !dmem_is_led;

// UART TX regs
reg  [7:0] uart_tx_data;
reg        uart_tx_start;
wire       uart_tx_busy;

// LED register
//reg  [7:0] led_reg;
//assign gpio_led = led_reg;

always @(posedge clk_mem or posedge reset) begin
    if (reset) begin
        uart_tx_start <= 1'b0;
        uart_tx_data  <= 8'h00;
        dbg_led       <= 8'h00;        // clear LEDs at reset
    end else begin
        uart_tx_start <= 1'b0;         // default

        if (dmem_is_uart && !uart_tx_busy) begin
            uart_tx_data  <= dmem_wdata[7:0];
            uart_tx_start <= 1'b1;
        end

        if (dmem_is_led) begin
            dbg_led <= dmem_wdata[7:0];   // LED MMIO
        end
    end
end


uart_tx_minimal #(
    .CLK_FREQ(100_000_000),
    .BAUD    (115200)
) u_tx_mmio (
    .clk   (clk_mem),
    .start (uart_tx_start),
    .data  (uart_tx_data),
    .tx    (uart_tx),
    .busy  (uart_tx_busy)
);

bram_dmem dmem (
    .clk   (clk_mem),
    .addr  (dmem_addr[15:2]),
    .wdata (dmem_wdata),
    .wstrb (dmem_we_real ? dmem_wstrb : 4'b0000),
    .rdata (dmem_rdata)
);

//=============================================================
// BRANCH PREDICTOR
//=============================================================

wire [31:0] predicted_pc;
wire        predicted_valid;

wire        branch_taken_ex1;
wire [31:0] branch_target_ex1;

branch_predictor bpu (
    .clk(clk_if1),
    .reset(reset),

    .if_pc(if1_pc),
    .predicted_pc(predicted_pc),
    .predicted_valid(predicted_valid),

    .branch_taken(branch_taken_ex1),
    .branch_pc      (ex1_pc), 
    .branch_target(branch_target_ex1)
);

//=============================================================
// IF1 STAGE
//=============================================================

wire flush_if = flush_id | flush_ex1;

if1 if1_stage (
    .clk_if1(clk_if1),
    .reset(reset),

    .stall_if(stall_if),
    .flush_if(flush_if),

    .branch_taken_ex(branch_taken_ex1),
    .branch_target_ex(branch_target_ex1),

    .predicted_pc(predicted_pc),
    .predicted_valid(predicted_valid),

    .pc_out(if1_pc),
    .if1_valid(if1_valid),
    .imem_addr()
);

//=============================================================
// IF2 STAGE
//=============================================================

if2 if2_stage (
    .clk_if2(clk_if2),
    .reset(reset),

    .if1_pc(if1_pc),
    .if1_instr(imem_rdata),
    .if1_valid(if1_valid),

    .stall_if2(stall_id),
    .flush_if2(flush_id),

    .id_pc(id_pc),
    .id_instr(id_instr),
    .id_valid(id_valid)
);

//=============================================================
//  RISC-V 7-Stage RV32IM Processor Top-Level
//  PART 2 / 4
//=============================================================


//=============================================================
// REGISTER FILE
//=============================================================
wire        rf_we;
wire [4:0]  rf_waddr;
wire [31:0] rf_wdata;
wire [4:0]  id_rs1_addr;
wire [4:0]  id_rs2_addr;
wire [31:0] id_rs1_data;
wire [31:0] id_rs2_data;

register_file rf (
    .clk(clk_wb),           // Writes occur in WB stage
    .we(rf_we),
    .waddr(rf_waddr),
    .wdata(rf_wdata),

    .raddr1(id_rs1_addr),
    .raddr2(id_rs2_addr),
    .rdata1(id_rs1_data),
    .rdata2(id_rs2_data)
);


//=============================================================
// HAZARD UNIT (RAW + load-use stalls)
//=============================================================

hazard_unit hazard (
    .id_valid(id_valid),
    .id_rs1(id_instr[19:15]),
    .id_rs2(id_instr[24:20]),

    .ex1_valid(ex1_valid),
    .ex1_rd(ex1_rd),
    .ex1_mem_read(ex1_ctrl_bus[14]),

    .ex2_valid(ex2_valid),
    .ex2_rd(ex2_rd),
    .ex2_mem_read(ex2_ctrl_bus[14]),

    .stall_if(stall_if),
    .stall_id(stall_id),
    .stall_ex1(stall_ex1),
    .flush_id(flush_id),
    .flush_ex1(flush_ex1),
    .mul_busy(mul_busy),
.div_busy(div_busy),
.branch_taken_ex1(branch_taken_ex1),
.predicted_valid(predicted_valid),
.predicted_pc(predicted_pc),
.branch_target(branch_target_ex1)
);


//=============================================================
// FORWARDING UNIT
//=============================================================

wire [31:0] fwd_rs1;
wire [31:0] fwd_rs2;

forwarding_unit fwd_unit (
    .id_rs1(id_instr[19:15]),
    .id_rs2(id_instr[24:20]),

    .ex2_valid(ex2_valid),
    .ex2_rd(ex2_rd),
    .ex2_result(mem_result), // Result of instruction in EX2

    .mem_valid(mem_valid),
    .mem_rd(mem_rd),
    .mem_result(wb_data),    // Result of instruction in MEM

    .wb_valid(wb_valid),
    .wb_rd(wb_rd),
    .wb_result(rf_wdata),    // Result of instruction in WB


    .fwd_rs1_val(fwd_rs1),
    .fwd_rs2_val(fwd_rs2),

    .original_rs1(id_rs1_data),
    .original_rs2(id_rs2_data)
);


//=============================================================
// ID STAGE
//=============================================================

wire is_branch_id;
wire is_load_id;
wire is_store_id;
wire is_mul_id;
wire is_div_id;
wire is_approx_id;

id id_stage (
    .clk_id(clk_id),
    .reset(reset),

    .id_pc_in(id_pc),
    .id_instr_in(id_instr),
    .id_valid_in(id_valid),

    .stall_id(stall_id),
    .flush_id(flush_id),

    .rs1_addr(id_rs1_addr),
    .rs2_addr(id_rs2_addr),
    .rs1_data(id_rs1_data),
    .rs2_data(id_rs2_data),

    .ex1_pc(ex1_pc),
    .ex1_rd(ex1_rd),
    .ex1_imm(ex1_imm),
    .ex1_instr(ex1_instr),
    .ex1_ctrl_bus(ex1_ctrl_bus),
    .ex1_valid(ex1_valid),

    .is_branch(is_branch_id),
    .is_load(is_load_id),
    .is_store(is_store_id),
    .is_mul(is_mul_id),
    .is_div(is_div_id),
    .is_approx(is_approx_id)
);


//=============================================================
// CSR + POWER MODE + APPROX MODE REGISTERS
//=============================================================

wire        wfi_active;

// Debug output

//=============================================================
//  RISC-V 7-Stage RV32IM Processor Top-Level
//  PART 3 / 4
//=============================================================


//=============================================================
// EX1 STAGE
//=============================================================

wire mul_start_ex1;
wire div_start_ex1;

ex1 ex1_stage (
    .clk_ex1(clk_ex1),
    .reset(reset),

    .ex1_valid_in(ex1_valid),
    .id_pc(ex1_pc),
    .id_instr(ex1_instr),
    .id_rs1(fwd_rs1),
    .id_rs2(fwd_rs2),
    .id_imm(ex1_imm),
    .id_rd(ex1_rd),
    .id_ctrl_bus(ex1_ctrl_bus),

    .fwd_rs1_val(fwd_rs1),
    .fwd_rs2_val(fwd_rs2),

    .stall_ex1(stall_ex1),
    .flush_ex1(flush_ex1),

    // EX1 → EX2 outputs
    .ex2_valid(ex2_valid),
    .ex2_pc(ex2_pc),
    .ex2_op_a(ex2_op_a),
    .ex2_op_b(ex2_op_b),
    .ex2_imm(ex2_imm),
    .ex2_instr(ex2_instr),
    .ex2_rd(ex2_rd),
    .ex2_ctrl_bus(ex2_ctrl_bus),
.ex2_store_data(ex2_store_data),
    // Branch resolution
    .branch_taken(branch_taken_ex1),
    .branch_target(branch_target_ex1),

    // MUL/DIV start
    .mul_start(mul_start_ex1),
    .div_start(div_start_ex1)
);


//=============================================================
// CSR UNIT
//=============================================================

wire [31:0] csr_rdata;
wire        csr_approx_mode;
wire [7:0]  csr_power_mode;

csr_unit core_csr (
    .clk(clk_sys),
    .reset(reset),

    .csr_op(ex2_ctrl_bus[9]),
    .csr_addr(ex2_instr[31:20]),
    .csr_funct3(ex2_instr[14:12]),
    .csr_wdata(ex2_op_a),
    .csr_rdata(csr_rdata),

    .inst_retired(wb_valid),
    
    .approx_mode(csr_approx_mode),
    .power_mode(csr_power_mode)
);

//=============================================================
// MULTIPLIER UNIT (DSP-Optimized)
//=============================================================

wire [31:0] mul_result;
wire        mul_busy;

mul_unit mul_u (
    .clk(clk_mul),
    .reset(reset),

    .start(mul_start_ex1),
    .op_type(ex2_ctrl_bus[18:16]),
    .op_a(ex2_op_a),
    .op_b(ex2_op_b),

    .result(mul_result),
    .busy(mul_busy)
);


//=============================================================
// DIVIDER UNIT (Iterative)
//=============================================================

wire [31:0] div_result;
wire        div_busy;

div_unit div_u (
    .clk(clk_div),
    .reset(reset),

    .start(div_start_ex1),
    .op_type(ex2_ctrl_bus[18:16]),
    .op_a(ex2_op_a),
    .op_b(ex2_op_b),

    .result(div_result),
    .busy(div_busy)
);


//=============================================================
// EX2 STAGE
//=============================================================

//wire stall_ex2;

ex2 ex2_stage (
    .clk_ex2(clk_ex2),
    .reset(reset),

    .ex2_valid_in(ex2_valid),
    .ex2_pc_in(ex2_pc),
    .ex2_op_a_in(ex2_op_a),
    .ex2_op_b_in(ex2_op_b),
    .ex2_instr_in(ex2_instr),
    .ex2_imm_in(ex2_imm),
    .ex2_rd_in(ex2_rd),
    .ex2_ctrl_bus_in(ex2_ctrl_bus),
    .mem_instr(mem_instr),

    .mul_start(mul_start_ex1),
    .div_start(div_start_ex1),

    .approx_enable(csr_approx_mode),

    .mul_result(mul_result),
    .mul_busy(mul_busy),
    .div_result(div_result),
    .div_busy(div_busy),

    .csr_rdata(csr_rdata),

    // Outputs to MEM
    .mem_valid(mem_valid),
    .mem_result(mem_result),
    .mem_pc(mem_pc),
    .mem_rd(mem_rd),
    .mem_ctrl_bus(mem_ctrl_bus),

    .stall_ex2(stall_ex2)
);


//=============================================================
// MEMORY STAGE (LOAD/STORE) with DMEM
//=============================================================

mem_stage mem_stg (
    .clk_mem(clk_mem),
    .reset(reset),

    .mem_valid_in(mem_valid),

    .ex2_result(mem_result),
    .ex2_op_b(ex2_store_data),
    .ex2_pc(mem_pc),
    .ex2_rd(mem_rd),
    .ex2_ctrl_bus(mem_ctrl_bus),
    .mem_instr_in(mem_instr),
    .wb_instr(wb_instr),

    // BRAM interface
    .mem_addr(dmem_addr),
    .mem_wdata(dmem_wdata),
    .mem_wstrb(dmem_wstrb),
    .mem_rdata(dmem_rdata),

    // Outputs to WB
    .wb_valid(wb_valid),
    .wb_result(wb_data),
    .wb_pc(wb_pc),
    .wb_rd(wb_rd),
    .wb_ctrl_bus(wb_ctrl_bus)
);

//=============================================================
//  RISC-V 7-Stage RV32IM Processor Top-Level
//  PART 4 / 4 - FINAL
//=============================================================


//=============================================================
// WRITEBACK (WB) STAGE
//=============================================================

wb_stage wb (
    .clk_wb(clk_wb),
    .reset(reset),

    .wb_valid_in(wb_valid),
    .wb_pc_in(wb_pc),
    .wb_data_in(wb_data),
    .wb_ctrl_bus_in(wb_ctrl_bus),
    .wb_rd_in(wb_rd),
    .wb_instr_in(wb_instr),  // instruction passes through EX2/MEM path

    // Register file write port
    .rf_we(rf_we),
    .rf_waddr(rf_waddr),
    .rf_wdata(rf_wdata),

    // WFI / Halt
    .wfi_active(wfi_active)
);



//=============================================================
// STAGE GATING CONTROLLER
//=============================================================

stage_gating_controller sg_ctrl (
    .clk(clk_sys),
    .reset(reset),

    // From ID (instruction class)
    .is_branch(is_branch_id),
    .is_load(is_load_id),
    .is_store(is_store_id),
    .is_mul(is_mul_id),
    .is_div(is_div_id),
    .is_approx(is_approx_id),

    // Stall + flush
    .stall_if(stall_if),
    .stall_id(stall_id),
    .stall_ex(stall_ex1 | stall_ex2),
    .flush_pipeline(flush_id | flush_ex1),

    // CSR power modes
    .pmode(csr_power_mode),
    .wfi_active(wfi_active),

    // MUL/DIV busy signals
    .mul_busy(mul_busy),
    .div_busy(div_busy),

    // CLOCK ENABLE OUTPUTS
    .ce_if1(ce_if1),
    .ce_if2(ce_if2),
    .ce_id(ce_id),
    .ce_ex1(ce_ex1),
    .ce_ex2(ce_ex2),
    .ce_mem(ce_mem),
    .ce_wb(ce_wb),

    .ce_mul(ce_mul),
    .ce_div(ce_div),
    .ce_approx(ce_approx),

    .ce_uart(ce_uart),
    .ce_csr(ce_csr)
);


//=============================================================
// DEBUG OUTPUTS
//=============================================================

//assign dbg_pc = if1_pc;
assign dbg_wfi_active = wfi_active;

// Simple LED debug - show lower 8 bits of writeback data
//assign dbg_led = rf_wdata[7:0];


//=============================================================
// END OF TOP-LEVEL
//=============================================================

endmodule
