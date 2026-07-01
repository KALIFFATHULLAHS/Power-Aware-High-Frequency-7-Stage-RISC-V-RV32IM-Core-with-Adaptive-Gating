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

    // No gating → all stages always enabled
    assign clk_if1    = clk_in & ce_if1;
    assign clk_if2    = clk_in & ce_if2;
    assign clk_id     = clk_in & ce_id;
    assign clk_ex1    = clk_in & ce_ex1;
    assign clk_ex2    = clk_in & ce_ex2;
    assign clk_mem    = clk_in & ce_mem;
    assign clk_wb     = clk_in & ce_wb;

    assign clk_mul    = clk_in & ce_mul;
    assign clk_div    = clk_in & ce_div;
    assign clk_approx = clk_in & ce_approx;

    assign clk_uart   = clk_in & ce_uart;
    assign clk_csr    = clk_in & ce_csr;

    // NO MMCM. NO BUFGCE. NO LOCKED.
    // This avoids X propagation.

`else
// -------------------------------------------------------------
// 2. FPGA SYNTHESIS MODE - Use real MMCM + BUFGCE
// -------------------------------------------------------------

    wire clk_fb, clk_mmcm_out;
    wire locked;

    MMCME2_BASE #(
        .CLKIN1_PERIOD(10.0),
        .CLKFBOUT_MULT_F(10.0),
        .DIVCLK_DIVIDE(1),
        .CLKOUT0_DIVIDE_F(10.0)
    ) mmcm_inst (
        .CLKIN1 (clk_in),
        .CLKFBIN(clk_fb),
        .CLKFBOUT(clk_fb),

        .CLKOUT0(clk_mmcm_out),

        .LOCKED(locked),

        .RST(reset),
        .PWRDWN(1'b0)
    );

    assign clk_sys = clk_mmcm_out;

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
