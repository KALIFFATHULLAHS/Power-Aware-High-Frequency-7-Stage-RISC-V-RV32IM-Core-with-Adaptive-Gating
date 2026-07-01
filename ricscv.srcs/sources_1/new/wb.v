`timescale 1ns/1ps

module wb_stage (
    input  wire        clk_wb,
    input  wire        reset,

    // From MEM
    input  wire        wb_valid_in,
    input  wire [31:0] wb_pc_in,
    input  wire [31:0] wb_data_in,
    input  wire [23:0] wb_ctrl_bus_in,
    input  wire [4:0]  wb_rd_in,
    input  wire [31:0] wb_instr_in,

    // Register File write port
    output reg         rf_we,
    output reg  [4:0]  rf_waddr,
    output reg  [31:0] rf_wdata,

    // WFI / Halt
    output reg         wfi_active
);

    wire reg_write = wb_ctrl_bus_in[15];

    //---------------------------------------------------------
    // WFI / SYSTEM CONTROL
    //---------------------------------------------------------
    wire is_csr = (wb_instr_in[6:0] == 7'b1110011);
    wire is_wfi = is_csr && (wb_instr_in[31:20] == 12'h105);

    always @(posedge clk_wb or posedge reset) begin
        if (reset) begin
            wfi_active <= 1'b0;
        end
        else if (wb_valid_in) begin
            if (is_wfi)
                wfi_active <= 1'b1;
            else
                wfi_active <= 1'b0;
        end
    end

    //---------------------------------------------------------
    // REGISTER FILE WRITEBACK
    //---------------------------------------------------------
    always @(posedge clk_wb or posedge reset) begin
        if (reset) begin
            rf_we    <= 0;
            rf_waddr <= 0;
            rf_wdata <= 0;
        end
        else if (wb_valid_in && reg_write && (wb_rd_in != 5'd0)) begin
            rf_we    <= 1;
            rf_waddr <= wb_rd_in;
            rf_wdata <= wb_data_in;
        end
        else begin
            rf_we <= 0;
        end
    end

endmodule

