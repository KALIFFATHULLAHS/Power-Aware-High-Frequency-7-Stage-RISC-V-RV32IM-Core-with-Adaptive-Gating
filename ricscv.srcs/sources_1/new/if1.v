`timescale 1ns/1ps

module if1 (
    input  wire        clk_if1,
    input  wire        reset,

    // From hazard unit
    input  wire        stall_if,
    input  wire        flush_if,

    // Branch mispredict feedback from EX2
    input  wire        branch_mispredict,
    input  wire [31:0] branch_recovery_pc,

    // Predictor feedback
    input  wire [31:0] predicted_pc,
    input  wire        predicted_valid,

    // Outputs to IF2
    output reg  [31:0] pc_out,
    output reg         if1_valid,
    output wire [31:0] if1_pred_pc,

    // To instruction memory
    output wire [31:0] imem_addr
);

    //---------------------------------------------------------
    // PROGRAM COUNTER REGISTER
    //---------------------------------------------------------
    reg [31:0] pc_reg;

    //---------------------------------------------------------
    // PC UPDATE LOGIC
    //---------------------------------------------------------
    wire [31:0] pc_next;

    assign pc_next =
        branch_mispredict    ? (branch_recovery_pc + 32'd4) :
        predicted_valid       ? (predicted_pc + 32'd4)       :
                                (pc_reg + 32'd4);

    assign if1_pred_pc = branch_mispredict ? branch_recovery_pc :
                         predicted_valid   ? predicted_pc       :
                                             pc_next;

    //---------------------------------------------------------
    // PC REGISTER UPDATE (clock-gated domain)
    //---------------------------------------------------------
    always @(posedge clk_if1 or posedge reset) begin
        if (reset) begin
            pc_reg    <= 32'h00000000;
            pc_out    <= 32'h00000000;
            if1_valid <= 1'b0;
        end else if (flush_if) begin
            pc_out    <= branch_mispredict ? branch_recovery_pc : pc_reg;
            pc_reg    <= branch_mispredict ? (branch_recovery_pc + 32'd4) : pc_next;
            if1_valid <= 1'b1;
        end else if (!stall_if) begin
            pc_out    <= predicted_valid ? predicted_pc : pc_reg;
            pc_reg    <= pc_next;
            if1_valid <= 1'b1;
        end
        // If stalled, hold values
    end

    //---------------------------------------------------------
    // Instruction Memory Address (Combinational address for synchronous BRAM read latency)
    //---------------------------------------------------------
    assign imem_addr = reset                ? 32'h00000000 :
                       branch_mispredict    ? branch_recovery_pc :
                       predicted_valid       ? predicted_pc       :
                                               pc_reg;

endmodule
