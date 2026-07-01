`timescale 1ns/1ps

module uart_tx_minimal #(
    parameter CLK_FREQ = 100_000_000,   // 100 MHz board clock
    parameter BAUD     = 115200
)(
    input  wire       clk,
    input  wire       start,            // pulse 1 cycle to start sending
    input  wire [7:0] data,             // byte to send
    output reg        tx   = 1'b1,      // UART TX line (idles high)
    output reg        busy = 1'b0       // 1 while shifting bits
);

    localparam integer DIVISOR = CLK_FREQ / BAUD;
    localparam integer CNT_W   = $clog2(DIVISOR);

    reg [CNT_W-1:0] baud_cnt = 0;
    reg [3:0]       bit_idx  = 0;
    reg [9:0]       shifter  = 10'b1111111111;

    always @(posedge clk) begin
        if (!busy) begin
            tx <= 1'b1;  // idle

            if (start) begin
                // start bit (0), data[7:0], stop bit (1)
                shifter <= {1'b1, data, 1'b0};
                busy    <= 1'b1;
                baud_cnt<= 0;
                bit_idx <= 0;
            end
        end else begin
            // we are in the middle of transmitting
            if (baud_cnt == DIVISOR-1) begin
                baud_cnt <= 0;

                tx      <= shifter[0];
                shifter <= {1'b1, shifter[9:1]};
                bit_idx <= bit_idx + 1;

                if (bit_idx == 4'd9) begin
                    busy <= 1'b0;   // finished 1 start + 8 data + 1 stop
                    tx   <= 1'b1;   // idle
                end
            end else begin
                baud_cnt <= baud_cnt + 1;
            end
        end
    end

endmodule
