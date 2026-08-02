`timescale 1ns/1ps

module clock_manager (
    input  wire clk_in,
    input  wire reset,

    // Gating enables
    input  wire ce_if1,
    input  wire ce_if2,
    input  wire ce_id,
    input  wire ce_ex1,
    input  wire ce_ex2,
    input  wire ce_mem,
    input  wire ce_wb,

    input  wire ce_mul,
    input  wire ce_div,
    input  wire ce_approx,

    input  wire ce_uart,
    input  wire ce_csr,

    // OUTPUT CLOCKS
    output wire clk_sys,

    output wire clk_if1,
    output wire clk_if2,
    output wire clk_id,
    output wire clk_ex1,
    output wire clk_ex2,
    output wire clk_mem,
    output wire clk_wb,

    output wire clk_mul,
    output wire clk_div,
    output wire clk_approx,

    output wire clk_uart,
    output wire clk_csr
);

// -------------------------------------------------------------
// 1. SIMULATION MODE - completely bypass MMCM and BUFGCE
// -------------------------------------------------------------
`ifndef SYNTHESIS
    // Direct clock
    assign clk_sys = clk_in;

    // Glitch-free simulation clock gating (negative latch ICG model)
    reg ce_if1_latch, ce_if2_latch, ce_id_latch, ce_ex1_latch, ce_ex2_latch, ce_mem_latch, ce_wb_latch;
    reg ce_mul_latch, ce_div_latch, ce_approx_latch, ce_uart_latch, ce_csr_latch;

    always @(*) begin
        if (!clk_in) begin
            ce_if1_latch    = ce_if1;
            ce_if2_latch    = ce_if2;
            ce_id_latch     = ce_id;
            ce_ex1_latch    = ce_ex1;
            ce_ex2_latch    = ce_ex2;
            ce_mem_latch    = ce_mem;
            ce_wb_latch     = ce_wb;
            ce_mul_latch    = ce_mul;
            ce_div_latch    = ce_div;
            ce_approx_latch = ce_approx;
            ce_uart_latch   = ce_uart;
            ce_csr_latch    = ce_csr;
        end
    end

    assign clk_if1    = clk_in & ce_if1_latch;
    assign clk_if2    = clk_in & ce_if2_latch;
    assign clk_id     = clk_in & ce_id_latch;
    assign clk_ex1    = clk_in & ce_ex1_latch;
    assign clk_ex2    = clk_in & ce_ex2_latch;
    assign clk_mem    = clk_in & ce_mem_latch;
    assign clk_wb     = clk_in & ce_wb_latch;

    assign clk_mul    = clk_in & ce_mul_latch;
    assign clk_div    = clk_in & ce_div_latch;
    assign clk_approx = clk_in & ce_approx_latch;

    assign clk_uart   = clk_in & ce_uart_latch;
    assign clk_csr    = clk_in & ce_csr_latch;

    // NO MMCM. NO BUFGCE. NO LOCKED.
    // This avoids X propagation.

`else
// -------------------------------------------------------------
// 2. FPGA SYNTHESIS MODE - Use real MMCM + BUFGCE
// -------------------------------------------------------------

    wire clk_fb, clk_mmcm_out;
    wire locked;

    MMCME2_BASE #(
        .CLKIN1_PERIOD(20.0),     // 50 MHz input clock (20.0 ns period)
        .CLKFBOUT_MULT_F(20.0),   // VCO = 50 MHz * 20 = 1000 MHz (valid range 600 - 1440 MHz)
        .DIVCLK_DIVIDE(1),
        .CLKOUT0_DIVIDE_F(20.0)   // clk_sys = 1000 MHz / 20 = 50 MHz
    ) mmcm_inst (
        .CLKIN1 (clk_in),
        .CLKFBIN(clk_fb),
        .CLKFBOUT(clk_fb),

        .CLKOUT0(clk_mmcm_out),

        .LOCKED(locked),

        .RST(1'b0),
        .PWRDWN(1'b0)
    );

    BUFG buf_sys (.I(clk_mmcm_out), .O(clk_sys));

    // Registered enables
    reg ce_if1_r, ce_if2_r, ce_id_r, ce_ex1_r, ce_ex2_r, ce_mem_r, ce_wb_r;
    reg ce_mul_r, ce_div_r, ce_approx_r;
    reg ce_uart_r, ce_csr_r;

    always @(posedge clk_mmcm_out or posedge reset) begin
        if (reset) begin
            ce_if1_r    <= 1;
            ce_if2_r    <= 1;
            ce_id_r     <= 1;
            ce_ex1_r    <= 1;
            ce_ex2_r    <= 1;
            ce_mem_r    <= 1;
            ce_wb_r     <= 1;
            ce_mul_r    <= 1;
            ce_div_r    <= 1;
            ce_approx_r <= 1;
            ce_uart_r   <= 1;
            ce_csr_r    <= 1;
        end else begin
            ce_if1_r    <= ce_if1;
            ce_if2_r    <= ce_if2;
            ce_id_r     <= ce_id;
            ce_ex1_r    <= ce_ex1;
            ce_ex2_r    <= ce_ex2;
            ce_mem_r    <= ce_mem;
            ce_wb_r     <= ce_wb;
            ce_mul_r    <= ce_mul;
            ce_div_r    <= ce_div;
            ce_approx_r <= ce_approx;
            ce_uart_r   <= ce_uart;
            ce_csr_r    <= ce_csr;
        end
    end

    // BUFGCE for FPGA  
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_if1 (.I(clk_mmcm_out), .CE(ce_if1_r), .O(clk_if1));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_if2 (.I(clk_mmcm_out), .CE(ce_if2_r), .O(clk_if2));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_id  (.I(clk_mmcm_out), .CE(ce_id_r ), .O(clk_id ));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_ex1 (.I(clk_mmcm_out), .CE(ce_ex1_r), .O(clk_ex1));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_ex2 (.I(clk_mmcm_out), .CE(ce_ex2_r), .O(clk_ex2));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_mem (.I(clk_mmcm_out), .CE(ce_mem_r), .O(clk_mem));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_wb  (.I(clk_mmcm_out), .CE(ce_wb_r ), .O(clk_wb ));

    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_mul    (.I(clk_mmcm_out), .CE(ce_mul_r), .O(clk_mul));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_div    (.I(clk_mmcm_out), .CE(ce_div_r), .O(clk_div));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_approx (.I(clk_mmcm_out), .CE(ce_approx_r), .O(clk_approx));

    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_uart (.I(clk_mmcm_out), .CE(ce_uart_r), .O(clk_uart));
    BUFGCE #(.SIM_DEVICE("7SERIES")) buf_csr  (.I(clk_mmcm_out), .CE(ce_csr_r ), .O(clk_csr));

`endif

endmodule
