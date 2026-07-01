`timescale 1ns/1ps

module if2 (
    input  wire        clk_if2,
    input  wire        reset,

    // From IF1
    input  wire [31:0] if1_pc,
    input  wire [31:0] if1_instr,
    input  wire        if1_valid,

    // Hazard and flush controls
    input  wire        stall_if2,
    input  wire        flush_if2,

    // Outputs to ID stage
    output reg  [31:0] id_pc,
    output reg  [31:0] id_instr,
    output reg         id_valid
);

    always @(posedge clk_if2 or posedge reset) begin
        if (reset) begin
            id_pc    <= 32'd0;
            id_instr <= 32'd0;
            id_valid <= 1'b0;
        end else if (flush_if2) begin
            id_pc    <= 32'd0;
            id_instr <= 32'd0;
            id_valid <= 1'b0;
        end else if (!stall_if2 && if1_valid) begin
            id_pc    <= if1_pc;
            id_instr <= if1_instr;
            id_valid <= 1'b1;
        end
        // If stalled → hold state
    end

endmodule
