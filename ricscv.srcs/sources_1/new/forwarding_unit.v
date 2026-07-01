`timescale 1ns/1ps

module forwarding_unit (
    // Sources required by EX1
    input  wire [4:0]  id_rs1,
    input  wire [4:0]  id_rs2,

    // EX2 forwarding path
    input  wire        ex2_valid,
    input  wire [4:0]  ex2_rd,
    input  wire [31:0] ex2_result,

    // MEM forwarding path
    input  wire        mem_valid,
    input  wire [4:0]  mem_rd,
    input  wire [31:0] mem_result,

    // WB forwarding path
    input  wire        wb_valid,
    input  wire [4:0]  wb_rd,
    input  wire [31:0] wb_result,

    // Original register file outputs
    input  wire [31:0] original_rs1,
    input  wire [31:0] original_rs2,

    // Output forwarded operands
    output reg [31:0] fwd_rs1_val,
    output reg [31:0] fwd_rs2_val
);

    always @(*) begin
        //-------------------------------------------
        // Source 1
        //-------------------------------------------
        if (ex2_valid && ex2_rd != 0 && ex2_rd == id_rs1)
            fwd_rs1_val = ex2_result;
        else if (mem_valid && mem_rd != 0 && mem_rd == id_rs1)
            fwd_rs1_val = mem_result;
        else if (wb_valid && wb_rd != 0 && wb_rd == id_rs1)
            fwd_rs1_val = wb_result;
        else
            fwd_rs1_val = original_rs1;

        //-------------------------------------------
        // Source 2
        //-------------------------------------------
        if (ex2_valid && ex2_rd != 0 && ex2_rd == id_rs2)
            fwd_rs2_val = ex2_result;
        else if (mem_valid && mem_rd != 0 && mem_rd == id_rs2)
            fwd_rs2_val = mem_result;
        else if (wb_valid && wb_rd != 0 && wb_rd == id_rs2)
            fwd_rs2_val = wb_result;
        else
            fwd_rs2_val = original_rs2;
    end

endmodule
