module stage_gating_controller (
    input  wire clk,
    input  wire reset,

    // From decode stage
    input  wire is_branch,
    input  wire is_load,
    input  wire is_store,
    input  wire is_mul,
    input  wire is_div,
    input  wire is_approx,

    // Hazard / stall inputs
    input  wire stall_if,
    input  wire stall_id,
    input  wire stall_ex,
    input  wire flush_pipeline,

    // CSR power modes
    input  wire [7:0] pmode,       // 8-bit mask from CSR
    input  wire       wfi_active,  // Wait-for-interrupt signal

    // MUL/DIV busy flags
    input  wire mul_busy,
    input  wire div_busy,

    // Clock enables (output)
    output reg ce_if1,
    output reg ce_if2,
    output reg ce_id,
    output reg ce_ex1,
    output reg ce_ex2,
    output reg ce_mem,
    output reg ce_wb,

    output reg ce_mul,
    output reg ce_div,
    output reg ce_approx,

    output reg ce_uart,
    output reg ce_csr
);

    always @(*) begin
        //----------------------------
        // DEFAULT: Use CSR pmode mask [6:0] for stages, [7] for UART
        //----------------------------
        ce_if1 = pmode[0];
        ce_if2 = pmode[1];
        ce_id  = pmode[2];
        ce_ex1 = pmode[3];
        ce_ex2 = pmode[4];
        ce_mem = pmode[5];
        ce_wb  = pmode[6];

        ce_mul    = pmode[4] & is_mul;
        ce_div    = pmode[4] & is_div;
        ce_approx = pmode[4] & is_approx;

        ce_uart = pmode[7];
        ce_csr  = 1'b1; // Always alive for interrupt wake

        //----------------------------
        // STALLS
        //----------------------------
        if (stall_if)
            ce_if1 = 0;

        if (stall_id)
            ce_if2 = 0;

        if (stall_ex) begin
            ce_ex1 = 0;
            ce_ex2 = 0;
        end

        //----------------------------
        // FLUSH
        //----------------------------
        if (flush_pipeline) begin
            ce_id  = 0;
            ce_ex1 = 0;
            ce_ex2 = 0;
        end

        //----------------------------
        // WFI MODE = FULL SHUTDOWN
        //----------------------------
        if (wfi_active) begin
            ce_if1 = 0;
            ce_if2 = 0;
            ce_id  = 0;
            ce_ex1 = 0;
            ce_ex2 = 0;
            ce_mem = 0;
            ce_wb  = 0;
        end
    end

endmodule

