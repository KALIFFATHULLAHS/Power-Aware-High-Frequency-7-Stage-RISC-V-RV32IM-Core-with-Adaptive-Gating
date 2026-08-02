`timescale 1ns/1ps

module hazard_unit (
    // ID stage info
    input  wire        id_valid,
    input  wire [4:0]  id_rs1,
    input  wire [4:0]  id_rs2,

    // EX1 stage
    input  wire        ex1_valid,
    input  wire [4:0]  ex1_rd,
    input  wire        ex1_mem_read,

    // EX2 stage
    input  wire        ex2_valid,
    input  wire [4:0]  ex2_rd,
    input  wire        ex2_mem_read,

    // MEM stage
    input  wire        mem_valid,
    input  wire [4:0]  mem_rd,
    input  wire        mem_mem_read,

    // Structural stalls
    input  wire        mul_busy,
    input  wire        div_busy,
    input  wire        stall_ex2,

    // Branch misprediction control
    input  wire        branch_mispredict,

    // Control outputs
    output reg         stall_if,
    output reg         stall_id,
    output reg         stall_ex1,
    output reg         flush_id,
    output reg         flush_ex1
);


    //===============================================
    // 1. LOAD-USE HAZARD
    //===============================================
    wire hazard_load_ex1 =
        ex1_valid && ex1_mem_read &&
        (ex1_rd != 0) &&
        (ex1_rd == id_rs1 || ex1_rd == id_rs2);

    wire hazard_load_ex2 =
        ex2_valid && ex2_mem_read &&
        (ex2_rd != 0) &&
        (ex2_rd == id_rs1 || ex2_rd == id_rs2);

    wire hazard_load_mem =
        mem_valid && mem_mem_read &&
        (mem_rd != 0) &&
        (mem_rd == id_rs1 || mem_rd == id_rs2);

    wire load_use_hazard = hazard_load_ex1 | hazard_load_ex2 | hazard_load_mem;

    //===============================================
    // 2. MULTI-CYCLE MUL/DIV STRUCTURAL HAZARDS
    //   These must stall EX1 and earlier stages.
    //===============================================
    wire muldiv_stall = mul_busy | div_busy;

    //===============================================
    // 3. FINAL STALL/FLUSH LOGIC
    //===============================================
    always @(*) begin
        // Default signals
        stall_if  = 0;
        stall_id  = 0;
        stall_ex1 = 0;

        flush_id  = 0;
        flush_ex1 = 0;

        //-------------------------------------------
        // LOAD-USE => Stall IF + ID, freeze EX1
        //-------------------------------------------
        if (load_use_hazard) begin
            stall_if  = 1;
            stall_id  = 1;
            stall_ex1 = 1;
        end

        //-------------------------------------------
        // MUL/DIV => Structural stall
        //-------------------------------------------
        if (muldiv_stall) begin
            stall_if  = 1;
            stall_id  = 1;
            stall_ex1 = 1;
        end

        //-------------------------------------------
        // EX2 STALL (from UART or Divider) => Stall all earlier stages
        //-------------------------------------------
        if (stall_ex2) begin
            stall_if  = 1;
            stall_id  = 1;
            stall_ex1 = 1;
        end

        //-------------------------------------------
        // BRANCH MISPREDICT => Flush ID and EX1
        //-------------------------------------------
        if (branch_mispredict) begin
            flush_id  = 1;
            flush_ex1 = 1;
        end
    end

endmodule
