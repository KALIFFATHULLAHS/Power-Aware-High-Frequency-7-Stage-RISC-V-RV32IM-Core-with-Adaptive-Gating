`timescale 1ns/1ps

module id (
    input  wire        clk_id,
    input  wire        reset,

    // From IF2
    input  wire [31:0] id_pc_in,
    input  wire [31:0] id_instr_in,
    input  wire        id_valid_in,

    // Hazard control
    input  wire        stall_id,
    input  wire        flush_id,

    // Register file interface
    output wire [4:0]  rs1_addr,
    output wire [4:0]  rs2_addr,
    input  wire [31:0] rs1_data,
    input  wire [31:0] rs2_data,

    // Outputs to EX1
    output reg  [31:0] ex1_pc,
    output reg  [31:0] ex1_rs1,
    output reg  [31:0] ex1_rs2,
    output reg  [4:0]  ex1_rd,
    output reg  [31:0] ex1_imm,
    output reg  [31:0] ex1_instr,
    output reg         ex1_valid,
    output reg  [23:0] ex1_ctrl_bus,

    // Instruction class → Power gating controller
    output reg is_branch,
    output reg is_load,
    output reg is_store,
    output reg is_mul,
    output reg is_div,
    output reg is_approx
);

    wire [6:0] opcode  = id_instr_in[6:0];
    wire [2:0] funct3  = id_instr_in[14:12];
    wire [6:0] funct7  = id_instr_in[31:25];
    wire [4:0] rd      = id_instr_in[11:7];
    wire [4:0] rs1     = id_instr_in[19:15];
    wire [4:0] rs2     = id_instr_in[24:20];

    assign rs1_addr = rs1;
    assign rs2_addr = rs2;

    //-----------------------------------------------------
    // IMMEDIATE GENERATION
    //-----------------------------------------------------
    reg [31:0] imm;

    always @(*) begin
        case (opcode)
            7'b0010011: imm = {{20{id_instr_in[31]}}, id_instr_in[31:20]}; // I-type
            7'b0000011: imm = {{20{id_instr_in[31]}}, id_instr_in[31:20]}; // Load
            7'b0100011: imm = {{20{id_instr_in[31]}}, id_instr_in[31:25], id_instr_in[11:7]}; // S-type
            7'b1100011: imm = {{19{id_instr_in[31]}}, id_instr_in[31], id_instr_in[7], id_instr_in[30:25], id_instr_in[11:8], 1'b0}; // B-type
            7'b1101111: imm = {{12{id_instr_in[31]}}, id_instr_in[19:12], id_instr_in[20], id_instr_in[30:21], 1'b0}; // J-type
            7'b1100111: imm = {{20{id_instr_in[31]}}, id_instr_in[31:20]}; // JALR
            7'b0110111: imm = {id_instr_in[31:12], 12'b0}; // U-type LUI
            7'b0010111: imm = {id_instr_in[31:12], 12'b0}; // U-type AUIPC
            default:     imm = 32'b0;
        endcase
    end

    //-----------------------------------------------------
    // INSTRUCTION CLASSIFICATION (for power gating)
    //-----------------------------------------------------
    always @(*) begin
        is_branch = (opcode == 7'b1100011);
        is_load   = (opcode == 7'b0000011);
        is_store  = (opcode == 7'b0100011);
        is_mul    = (opcode == 7'b0110011 && funct7 == 7'b0000001 && funct3[2] == 1'b0);
        is_div    = (opcode == 7'b0110011 && funct7 == 7'b0000001 && funct3[2] == 1'b1);
        is_approx = (opcode == 7'b0001011);
    end

    // ---------------- CONTROL SIGNAL GENERATION -----------------------
    reg [23:0] ctrl_bus_dec;  

    always @(*) begin
        ctrl_bus_dec = 24'b0;

        case (opcode)
            7'b0110011: begin // R-type
                ctrl_bus_dec[15] = 1'b1; // reg_write
                if (funct7 == 7'b0000001) begin // M-extension
                    ctrl_bus_dec[23] = 1'b1; // is_m_ext
                    ctrl_bus_dec[19:16] = {1'b0, funct3}; 
                end else begin
                    ctrl_bus_dec[7:4] = {funct7[5], funct3}; 
                end
            end
            7'b0010011: begin // I-type ALU
                ctrl_bus_dec[15] = 1'b1; // reg_write
                ctrl_bus_dec[8]  = 1'b1; // alu_src_b (imm)
                if (funct3 == 3'b101 || funct3 == 3'b001)
                    ctrl_bus_dec[7:4] = {funct7[5], funct3};
                else
                    ctrl_bus_dec[7:4] = {1'b0, funct3};
            end
            7'b0000011: begin // Load
                ctrl_bus_dec[15] = 1'b1; // reg_write
                ctrl_bus_dec[14] = 1'b1; // mem_read
                ctrl_bus_dec[10:8] = funct3; 
            end
            7'b0100011: begin // Store
                ctrl_bus_dec[13] = 1'b1; // mem_write
                ctrl_bus_dec[10:8] = funct3;
            end
            7'b1100011: begin // Branch
                ctrl_bus_dec[12] = 1'b1; 
            end
            7'b1101111: begin // JAL
                ctrl_bus_dec[15] = 1'b1; 
                ctrl_bus_dec[11] = 1'b1; // jump
            end
            7'b1100111: begin // JALR
                ctrl_bus_dec[15] = 1'b1; 
                ctrl_bus_dec[10] = 1'b1; // jalr
            end
            7'b0110111: begin // LUI
                ctrl_bus_dec[15] = 1'b1; 
                ctrl_bus_dec[7:4] = 4'b1111; // LUI
            end
            7'b0010111: begin // AUIPC
                ctrl_bus_dec[15] = 1'b1; 
                ctrl_bus_dec[7:4] = 4'b1110; // AUIPC
            end
            7'b1110011: begin // SYSTEM (CSR)
                ctrl_bus_dec[15] = (funct3 != 3'b000); 
                ctrl_bus_dec[9] = 1'b1; // csr_op
            end
        endcase
    end


    // ---------------- PIPELINE REGISTER (ID → EX1) --------------------
    always @(posedge clk_id or posedge reset) begin
        if (reset) begin
            ex1_pc       <= 32'b0;
            ex1_rs1      <= 32'b0;
            ex1_rs2      <= 32'b0;
            ex1_rd       <= 5'b0;
            ex1_imm      <= 32'b0;
            ex1_instr    <= 32'b0;
            ex1_ctrl_bus <= 16'b0;
            ex1_valid    <= 1'b0;
        end
        else if (flush_id) begin
            ex1_valid    <= 1'b0;
        end
        else if (!stall_id && id_valid_in) begin
            ex1_pc       <= id_pc_in;
            ex1_rs1      <= rs1_data;
            ex1_rs2      <= rs2_data;
            ex1_rd       <= rd;
            ex1_imm      <= imm;
            ex1_instr    <= id_instr_in;
            ex1_ctrl_bus <= ctrl_bus_dec;   // ✅ load decoded control
            ex1_valid    <= 1'b1;
        end
    end
endmodule