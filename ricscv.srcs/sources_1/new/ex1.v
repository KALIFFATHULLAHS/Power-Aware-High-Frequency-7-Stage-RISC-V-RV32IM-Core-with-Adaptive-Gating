`timescale 1ns/1ps

module ex1 (
    input  wire        clk_ex1,
    input  wire        reset,

    // From ID stage
    input  wire        ex1_valid_in,
    input  wire [31:0] id_pc,
    input  wire [31:0] id_instr,
    input  wire [31:0] id_rs1,
    input  wire [31:0] id_rs2,
    input  wire [31:0] id_imm,
    input  wire [4:0]  id_rd,
    input  wire [23:0] id_ctrl_bus,

    // After Forwarding
    input  wire [31:0] fwd_rs1_val,
    input  wire [31:0] fwd_rs2_val,

    // Hazard control
    input  wire        stall_ex1,
    input  wire        flush_ex1,

    // Outputs to EX2
    output reg         ex2_valid,
    output reg [31:0]  ex2_pc,
    output reg [31:0]  ex2_op_a,
    output reg [31:0]  ex2_op_b,          // ALU operand B (IMM or rs2)
    output reg [31:0]  ex2_imm,
    output reg [31:0]  ex2_instr,
    output reg [4:0]   ex2_rd,
    output reg [23:0]  ex2_ctrl_bus,

    // Branch resolution
    output reg         branch_taken,
    output reg [31:0]  branch_target,

    // MUL/DIV requests
    output reg         mul_start,
    output reg         div_start,

    // *** FIXED: STORE DATA PATH ***
    output reg [31:0]  ex2_store_data
);

    //------------------------------------------------------------
    // Field extraction
    //------------------------------------------------------------
    wire [6:0] opcode = id_instr[6:0];
    wire [2:0] funct3 = id_instr[14:12];
    wire [6:0] funct7 = id_instr[31:25];

    wire        is_branch = id_ctrl_bus[12];
    wire        is_jump   = id_ctrl_bus[11];
    wire        is_jalr   = id_ctrl_bus[10];
    wire        is_muldiv = id_ctrl_bus[23];

    //------------------------------------------------------------
    // Operand A (always rs1 forwarded)
    //------------------------------------------------------------
    wire [31:0] op_a = fwd_rs1_val;

    //------------------------------------------------------------
    // ALU Operand B
    //------------------------------------------------------------
    wire [31:0] alu_op_b = id_ctrl_bus[8] ? id_imm : fwd_rs2_val;

    //------------------------------------------------------------
    // Store data
    //------------------------------------------------------------
    wire [31:0] store_data = fwd_rs2_val;

    //------------------------------------------------------------
    // Branch decision
    //------------------------------------------------------------
    reg branch_result;

    always @(*) begin
        if (is_branch) begin
            case (funct3)
                3'b000: branch_result = (op_a == fwd_rs2_val);                   // BEQ
                3'b001: branch_result = (op_a != fwd_rs2_val);                   // BNE
                3'b100: branch_result = ($signed(op_a) <  $signed(fwd_rs2_val)); // BLT
                3'b101: branch_result = ($signed(op_a) >= $signed(fwd_rs2_val)); // BGE
                3'b110: branch_result = (op_a <  fwd_rs2_val);                   // BLTU
                3'b111: branch_result = (op_a >= fwd_rs2_val);                   // BGEU
                default: branch_result = 0;
            endcase
        end else begin
            branch_result = 0;
        end
    end

    // Branch/Jump Target
    wire [31:0] target_base = is_jalr ? fwd_rs1_val : id_pc;
    wire [31:0] calc_branch_target = (target_base + id_imm) & (is_jalr ? 32'hFFFFFFFE : 32'hFFFFFFFF);

    //------------------------------------------------------------
    // PIPELINE REGISTER: EX1 → EX2
    //------------------------------------------------------------
    always @(posedge clk_ex1 or posedge reset) begin
        if (reset) begin
            ex2_valid       <= 0;
            mul_start       <= 0;
            div_start       <= 0;
            branch_taken    <= 0;
            branch_target   <= 0;
            ex2_store_data  <= 0;
        end
        else if (flush_ex1) begin
            ex2_valid     <= 0;      // bubble
            mul_start     <= 0;
            div_start     <= 0;
            branch_taken  <= 0;
        end
        else if (!stall_ex1) begin
            ex2_valid    <= ex1_valid_in;
            ex2_pc       <= id_pc;
            ex2_op_a     <= op_a;
            ex2_op_b     <= alu_op_b;
            ex2_imm      <= id_imm;
            ex2_instr    <= id_instr;
            ex2_rd       <= id_rd;
            ex2_ctrl_bus <= id_ctrl_bus;

            ex2_store_data <= store_data;

            branch_taken  <= branch_result | is_jump | is_jalr;
            branch_target <= calc_branch_target;

            mul_start <= is_muldiv && !id_ctrl_bus[18]; // bit 18 of ctrl is funct3[2]
            div_start <= is_muldiv &&  id_ctrl_bus[18];
        end
    end


endmodule
