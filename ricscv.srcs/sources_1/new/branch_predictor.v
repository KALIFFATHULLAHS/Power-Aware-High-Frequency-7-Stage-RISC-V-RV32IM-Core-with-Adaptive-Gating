`timescale 1ns/1ps

module branch_predictor (
    input  wire        clk,
    input  wire        reset,

    // From IF1
    input  wire [31:0] if_pc,

    // Prediction output
    output reg  [31:0] predicted_pc,
    output reg         predicted_valid,

    // Feedback from EX1 (resolution)
    input  wire        branch_taken,
    input  wire [31:0] branch_pc,
    input  wire [31:0] branch_target
);

    // BHT: 256 entries of 2-bit saturating counters
    reg [1:0] bht[255:0];

    // BTB: holds predicted targets
    reg [31:0] btb[255:0];

    wire [7:0] index = if_pc[9:2];

    //---------------------------------------------------------
    // PREDICT
    //---------------------------------------------------------
    always @(*) begin
        if (bht[index] >= 2) begin
            predicted_valid = 1;
            predicted_pc    = btb[index];
        end else begin
            predicted_valid = 0;
            predicted_pc    = if_pc + 4;
        end
    end

    //---------------------------------------------------------
    // UPDATE ON RESOLUTION
    //---------------------------------------------------------
    wire [7:0] idx2 = branch_pc[9:2];
    integer i;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            
            for (i=0; i<256; i=i+1) begin
                bht[i] <= 2'b01; // weak not taken
                btb[i] <= 0;
            end
        end else begin
            if (branch_taken) begin
                if (bht[idx2] != 2'b11)
                    bht[idx2] <= bht[idx2] + 1;
                btb[idx2] <= branch_target;
            end else begin
                if (bht[idx2] != 2'b00)
                    bht[idx2] <= bht[idx2] - 1;
            end
        end
    end

endmodule
