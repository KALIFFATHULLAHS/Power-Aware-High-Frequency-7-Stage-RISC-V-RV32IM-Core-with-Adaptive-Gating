`timescale 1ns/1ps

module branch_predictor (
    input  wire        clk,
    input  wire        reset,

    // From IF1
    input  wire [31:0] if_pc,

    // Prediction output
    output reg  [31:0] predicted_pc,
    output reg         predicted_valid,

    // Feedback from EX2 (resolution)
    input  wire        is_branch_instr,
    input  wire        branch_taken,
    input  wire [31:0] branch_pc,
    input  wire [31:0] branch_target
);

    // 64-entry BHT + BTB with Tag matching
    reg [1:0]  bht [63:0];
    reg [31:0] btb [63:0];
    reg [31:0] tag [63:0];

    wire [5:0] if_idx  = if_pc[7:2];
    wire [5:0] ex2_idx = branch_pc[7:2];

    //---------------------------------------------------------
    // PREDICT
    //---------------------------------------------------------
    always @(*) begin
        if (!reset && (bht[if_idx] >= 2'b10) && (tag[if_idx] == if_pc)) begin
            predicted_valid = 1'b1;
            predicted_pc    = btb[if_idx];
        end else begin
            predicted_valid = 1'b0;
            predicted_pc    = if_pc + 32'd4;
        end
    end

    //---------------------------------------------------------
    // UPDATE ON RESOLUTION & RESET
    //---------------------------------------------------------
    integer i;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (i = 0; i < 64; i = i + 1) begin
                bht[i] <= 2'b01; // Weakly Not Taken
                btb[i] <= 32'd0;
                tag[i] <= 32'hFFFF_FFFF; // Invalid tag
            end
        end else if (is_branch_instr) begin
            if (branch_taken) begin
                if (bht[ex2_idx] != 2'b11)
                    bht[ex2_idx] <= bht[ex2_idx] + 1'b1;
                btb[ex2_idx] <= branch_target;
                tag[ex2_idx] <= branch_pc;
            end else begin
                if (bht[ex2_idx] != 2'b00)
                    bht[ex2_idx] <= bht[ex2_idx] - 1'b1;
            end
        end
    end

endmodule
