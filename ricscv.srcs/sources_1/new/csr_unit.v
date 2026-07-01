`timescale 1ns/1ps

module csr_unit (
    input  wire        clk,
    input  wire        reset,

    // CSR access interface (from EX2)
    input  wire        csr_op,           // Enable CSR operation
    input  wire [11:0] csr_addr,
    input  wire [2:0]  csr_funct3,       // RW, RS, RC
    input  wire [31:0] csr_wdata,
    output reg  [31:0] csr_rdata,

    // Performance inputs
    input  wire        inst_retired,     // 1 if an instruction finished WB this cycle

    // Special control outputs
    output reg         approx_mode,
    output reg [7:0]   power_mode
);

    // Standard CSRs
    reg [63:0] mcycle;
    reg [63:0] minstret;

    // Custom CSRs
    reg [31:0] mapprox;
    reg [31:0] mpower;

    // Cycle counter
    always @(posedge clk) begin
        if (reset) mcycle <= 64'd0;
        else       mcycle <= mcycle + 1;
    end

    // Instruction counter
    always @(posedge clk) begin
        if (reset) minstret <= 64'd0;
        else if (inst_retired) minstret <= minstret + 1;
    end

    // CSR Read
    always @(*) begin
        case (csr_addr)
            12'hC00: csr_rdata = mcycle[31:0];
            12'hC80: csr_rdata = mcycle[63:32];
            12'hC02: csr_rdata = minstret[31:0];
            12'hC82: csr_rdata = minstret[63:32];
            12'h800: csr_rdata = mapprox;
            12'h801: csr_rdata = mpower;
            default: csr_rdata = 32'd0;
        endcase
    end

    // CSR Write
    always @(posedge clk) begin
        if (reset) begin
            mapprox <= 32'd0;
            mpower  <= 32'hFF; // All stages enabled by default
            approx_mode <= 0;
            power_mode  <= 8'hFF;
        end else if (csr_op) begin
            case (csr_funct3[1:0])
                2'b01: begin // CSRRW
                    case (csr_addr)
                        12'h800: mapprox <= csr_wdata;
                        12'h801: mpower  <= csr_wdata;
                    endcase
                end
                2'b10: begin // CSRRS
                    case (csr_addr)
                        12'h800: mapprox <= mapprox | csr_wdata;
                        12'h801: mpower  <= mpower  | csr_wdata;
                    endcase
                end
                2'b11: begin // CSRRC
                    case (csr_addr)
                        12'h800: mapprox <= mapprox & ~csr_wdata;
                        12'h801: mpower  <= mpower  & ~csr_wdata;
                    endcase
                end
            endcase
            
            approx_mode <= mapprox[0];
            power_mode  <= mpower[7:0];
        end
    end

endmodule
