`timescale 1ns/1ps

module mem_stage (
    input  wire        clk_mem,
    input  wire        reset,

    // From EX2
    input  wire        mem_valid_in,
    input  wire [31:0] ex2_result,
    input  wire [31:0] ex2_op_b,         // store data
    input  wire [31:0] ex2_pc,
    input  wire [4:0]  ex2_rd,
    input  wire [23:0] ex2_ctrl_bus,
    input  wire [31:0] mem_instr_in,
    
    // Memory interface (BRAM)
    output reg  [31:0] mem_addr,
    output reg  [31:0] mem_wdata,
    output reg  [3:0]  mem_wstrb,
    input  wire [31:0] mem_rdata,
    output reg  [31:0] wb_instr,
    // Pipeline output to WB
    output reg         wb_valid,
    output reg  [31:0] wb_result,
    output reg  [31:0] wb_pc,
    output reg  [4:0]  wb_rd,
    output reg  [23:0] wb_ctrl_bus
);

    //---------------------------------------------------------
    // Unpack control signals
    //---------------------------------------------------------
    wire reg_write = ex2_ctrl_bus[15];
    wire mem_read  = ex2_ctrl_bus[14];
    wire mem_write = ex2_ctrl_bus[13];

    //---------------------------------------------------------
    // STORE WRITE STROBE AND DATA PACKING
    //---------------------------------------------------------
    reg [31:0] store_data;
    reg [3:0]  store_strb;

    always @(*) begin
        store_data = 0;
        store_strb = 0;

        case (ex2_ctrl_bus[10:8])   // funct3 for store
    3'b000: begin // SB
        store_strb = (4'b0001 << ex2_result[1:0]);
        store_data = {4{ex2_op_b[7:0]}};
    end
    3'b001: begin // SH
        store_strb = (ex2_result[1] == 1'b0) ? 4'b0011 : 4'b1100;
        store_data = {2{ex2_op_b[15:0]}};
    end
    3'b010: begin // SW
        store_strb = 4'b1111;
        store_data = ex2_op_b;
    end
    default: begin
        store_strb = 4'b0000;  // illegal store size -> do nothing
        store_data = 32'd0;
    end
endcase
    end

    //---------------------------------------------------------
    // LOAD SIGN EXTENSION
    //---------------------------------------------------------
    reg [31:0] load_data;

    always @(*) begin
       case (ex2_ctrl_bus[10:8])  // funct3 for load
    3'b000: begin // LB
        case (ex2_result[1:0])
            2'b00: load_data = {{24{mem_rdata[7]}},  mem_rdata[7:0]};
            2'b01: load_data = {{24{mem_rdata[15]}}, mem_rdata[15:8]};
            2'b10: load_data = {{24{mem_rdata[23]}}, mem_rdata[23:16]};
            default: load_data = {{24{mem_rdata[31]}}, mem_rdata[31:24]};
        endcase
    end
    3'b001: begin // LH
        if (ex2_result[1] == 1'b0)
            load_data = {{16{mem_rdata[15]}}, mem_rdata[15:0]};
        else
            load_data = {{16{mem_rdata[31]}}, mem_rdata[31:16]};
    end
    3'b010: begin // LW
        load_data = mem_rdata;
    end
    3'b100: begin // LBU
        case (ex2_result[1:0])
            2'b00: load_data = {24'd0, mem_rdata[7:0]};
            2'b01: load_data = {24'd0, mem_rdata[15:8]};
            2'b10: load_data = {24'd0, mem_rdata[23:16]};
            default: load_data = {24'd0, mem_rdata[31:24]};
        endcase
    end
    3'b101: begin // LHU
        if (ex2_result[1] == 1'b0)
            load_data = {16'd0, mem_rdata[15:0]};
        else
            load_data = {16'd0, mem_rdata[31:16]};
    end
    default: load_data = 32'd0;
endcase
    end

    //---------------------------------------------------------
    // PIPELINE REGISTER (MEM → WB)
    //---------------------------------------------------------
    //---------------------------------------------------------
    // BRAM INTERFACE (COMBINATORIAL)
    //---------------------------------------------------------
    always @(*) begin
        if (mem_valid_in) begin
            mem_addr  = ex2_result;
            if (mem_write) begin
                mem_wdata = store_data;
                mem_wstrb = store_strb;
            end else begin
                mem_wdata = 0;
                mem_wstrb = 0;
            end
        end else begin
            mem_addr  = 0;
            mem_wdata = 0;
            mem_wstrb = 0;
        end
    end

    //---------------------------------------------------------
    // PIPELINE REGISTER (MEM → WB)
    //---------------------------------------------------------
    always @(posedge clk_mem or posedge reset) begin
        if (reset) begin
            wb_valid <= 0;
            wb_pc    <= 0;
            wb_rd    <= 0;
            wb_ctrl_bus <= 0;
            wb_instr <= 0;
            wb_result <= 0;
        end
        else if (mem_valid_in) begin
            wb_valid    <= 1;
            wb_pc       <= ex2_pc;
            wb_rd       <= ex2_rd;
            wb_ctrl_bus <= ex2_ctrl_bus;
            wb_instr    <= mem_instr_in;

            wb_result   <= (mem_read) ? load_data : ex2_result;
        end else begin
            wb_valid <= 0;
        end
    end


endmodule
