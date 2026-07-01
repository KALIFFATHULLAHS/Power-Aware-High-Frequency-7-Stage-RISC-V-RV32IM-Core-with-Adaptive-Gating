`timescale 1ns/1ps

module ex2 (
    input  wire        clk_ex2,
    input  wire        reset,

    // From EX1 (pipeline inputs)
    input  wire        ex2_valid_in,
    input  wire [31:0] ex2_pc_in,
    input  wire [31:0] ex2_op_a_in,
    input  wire [31:0] ex2_op_b_in,
    input  wire [31:0] ex2_instr_in,
    input  wire [31:0] ex2_imm_in,
    input  wire [4:0]  ex2_rd_in,
    input  wire [23:0] ex2_ctrl_bus_in,

    // MUL/DIV start pulse from EX1
    input  wire        mul_start,
    input  wire        div_start,

    // Approx ALU enable
    input  wire        approx_enable,

    // MUL/DIV execution units
    input  wire [31:0] mul_result,
    input  wire        mul_busy,
    input  wire [31:0] div_result,
    input  wire        div_busy,

    // CSR unit
    input  wire [31:0] csr_rdata,

    // Outputs to MEM stage
    output reg         mem_valid,
    output reg [31:0]  mem_result,
    output reg [31:0]  mem_pc,
    output reg [4:0]   mem_rd,
    output reg [23:0]  mem_ctrl_bus,
    output reg [31:0]  mem_instr,

    // Stall indicator to EX1 / front pipeline
    output wire        stall_ex2
);

    //-----------------------------------------------------
    // Detect instruction fields
    //-----------------------------------------------------
    wire [6:0]  opcode = ex2_instr_in[6:0];
    wire [2:0]  funct3 = ex2_instr_in[14:12];
    wire [6:0]  funct7 = ex2_instr_in[31:25];

    wire        is_jump = ex2_ctrl_bus_in[11];
    wire        is_jalr = ex2_ctrl_bus_in[10];
    wire        is_csr  = ex2_ctrl_bus_in[9];

    //-----------------------------------------------------
    // EX2 stall logic for MUL/DIV
    //-----------------------------------------------------
    assign stall_ex2 =
        (mul_start && mul_busy) ||
        (div_start && div_busy);

    //-----------------------------------------------------
    // ALU Implementation
    //-----------------------------------------------------

    reg [31:0] alu_exact;
    reg [31:0] alu_approx;

    always @(*) begin
        alu_exact = 32'd0;
        if (is_csr) begin
            alu_exact = csr_rdata;
        end else begin
            case (ex2_ctrl_bus_in[7:4])
                4'b0000: alu_exact = ex2_op_a_in + ex2_op_b_in;                               // ADD
                4'b1000: alu_exact = ex2_op_a_in - ex2_op_b_in;                               // SUB
                4'b0001: alu_exact = ex2_op_a_in << ex2_op_b_in[4:0];                         // SLL
                4'b0010: alu_exact = ($signed(ex2_op_a_in) < $signed(ex2_op_b_in)) ? 32'd1 : 32'd0; // SLT
                4'b0011: alu_exact = (ex2_op_a_in < ex2_op_b_in) ? 32'd1 : 32'd0;             // SLTU
                4'b0100: alu_exact = ex2_op_a_in ^ ex2_op_b_in;                               // XOR
                4'b0101: alu_exact = ex2_op_a_in >> ex2_op_b_in[4:0];                          // SRL
                4'b1101: alu_exact = $signed(ex2_op_a_in) >>> ex2_op_b_in[4:0];                // SRA
                4'b0110: alu_exact = ex2_op_a_in | ex2_op_b_in;                               // OR
                4'b0111: alu_exact = ex2_op_a_in & ex2_op_b_in;                               // AND
                4'b1111: alu_exact = ex2_imm_in;                                              // LUI
                4'b1110: alu_exact = ex2_pc_in + ex2_imm_in;                                  // AUIPC
                default: alu_exact = 32'd0;
            endcase
        end
    end


    // Approx ALU (truncating 4 LSBs)
    always @(*) begin
        alu_approx = { (ex2_op_a_in[31:4] + ex2_op_b_in[31:4]), 4'b0000 };
    end

    wire [31:0] alu_final = (approx_enable && !ex2_ctrl_bus_in[8]) ? alu_approx : alu_exact;

    //-----------------------------------------------------
    // EX2 → MEM pipeline register
    //-----------------------------------------------------
    always @(posedge clk_ex2 or posedge reset) begin
        if (reset) begin
            mem_valid    <= 0;
            mem_result   <= 32'd0;
            mem_pc       <= 32'd0;
            mem_rd       <= 5'd0;
            mem_ctrl_bus <= 24'd0;
            mem_instr    <= 32'd0;
        end 
        else if (!stall_ex2 && ex2_valid_in) begin
            mem_valid    <= 1;
            mem_pc       <= ex2_pc_in;
            mem_rd       <= ex2_rd_in;
            mem_ctrl_bus <= ex2_ctrl_bus_in;
            mem_instr    <= ex2_instr_in;

            if (is_jump || is_jalr)
                mem_result <= ex2_pc_in + 4;
            else if (mul_start)
                mem_result <= mul_result;
            else if (div_start)
                mem_result <= div_result;
            else
                mem_result <= alu_final;
        end else begin
            mem_valid <= 0;
        end
    end


endmodule
