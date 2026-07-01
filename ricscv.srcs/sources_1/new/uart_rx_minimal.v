`timescale 1ns/1ps
module uart_rx #(
    parameter CLK_FREQ  = 100_000_000,
    parameter BAUD_RATE = 115200
)(
    input  wire       clk,
    input  wire       rx,
    output reg        data_valid,
    output reg [7:0]  data_byte
);

    localparam integer DIVISOR = CLK_FREQ / BAUD_RATE;

    // States
    localparam IDLE  = 2'd0;
    localparam START = 2'd1;
    localparam DATA  = 2'd2;
    localparam STOP  = 2'd3;

    reg [1:0]  state = IDLE;
    reg [$clog2(DIVISOR):0] clk_cnt = 0;   // enough width
    reg [2:0]  bit_idx = 0;
    reg [7:0]  shift   = 0;

    always @(posedge clk) begin
        data_valid <= 1'b0;

        case (state)
            //-------------------------------------------------
            // IDLE: wait for start bit (rx goes low)
            //-------------------------------------------------
            IDLE: begin
                clk_cnt <= 0;
                bit_idx <= 0;
                if (rx == 1'b0) begin
                    // start bit detected, go to START
                    state   <= START;
                    clk_cnt <= 0;
                end
            end

            //-------------------------------------------------
            // START: wait HALF bit time, then confirm start
            //-------------------------------------------------
            START: begin
                if (clk_cnt == (DIVISOR/2)) begin
                    clk_cnt <= 0;
                    if (rx == 1'b0) begin
                        // valid start bit
                        state <= DATA;
                    end else begin
                        // glitch, go back to idle
                        state <= IDLE;
                    end
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end

            //-------------------------------------------------
            // DATA: sample 8 bits, each at bit center
            //-------------------------------------------------
            DATA: begin
                if (clk_cnt == (DIVISOR-1)) begin
                    clk_cnt <= 0;

                    // sample one data bit (LSB first)
                    shift   <= {rx, shift[7:1]};
                    bit_idx <= bit_idx + 1;

                    if (bit_idx == 3'd7) begin
                        state <= STOP;
                    end
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end

            //-------------------------------------------------
            // STOP: wait 1 bit, then accept byte
            //-------------------------------------------------
            STOP: begin
                if (clk_cnt == (DIVISOR-1)) begin
                    clk_cnt <= 0;

                    // optional stop bit check: rx should be 1
                    data_byte  <= shift;
                    data_valid <= 1'b1;
                    state      <= IDLE;
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end

            default: state <= IDLE;
        endcase
    end

endmodule