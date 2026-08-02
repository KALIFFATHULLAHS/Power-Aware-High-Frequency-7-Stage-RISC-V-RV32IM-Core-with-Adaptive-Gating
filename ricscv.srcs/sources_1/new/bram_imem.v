module bram_imem(
    input  wire        clk,          // CPU clock
    input  wire [13:0] addr,
    output reg  [31:0] rdata,

    input  wire        reset,        // Reset signal for bootloader
    input  wire        uart_clk,     // UART clock
    input  wire        uart_rx,
    output wire        uart_tx       // not used here but kept if needed
);

    // 4K words (16KB)
    (* ram_style = "block" *) reg [31:0] mem [0:4095];

    integer i;
    initial begin
        for (i = 0; i < 4096; i = i + 1) begin
            mem[i] = 32'h00000013; // Initialize entire memory to RISC-V NOPs (addi x0, x0, 0)
        end
        $display("[BRAM] Memory initialized with NOPs successfully.");
    end

    //--------------------------------------------------
    // PORT A: CPU READ PORT (clk_sys)
    //--------------------------------------------------
    always @(posedge clk) begin
        rdata <= mem[addr];
    end

    //--------------------------------------------------
    // UART RX + WRITE LOGIC
    //--------------------------------------------------

    wire [7:0] rx_byte;
    wire       rx_valid;

  uart_rx #(
    .CLK_FREQ(50_000_000),
    .BAUD_RATE(115200)
) u_rx (
    .clk(uart_clk),
    .rx(uart_rx),
    .data_valid(rx_valid),
    .data_byte(rx_byte)
);

    reg [31:0] assemble_word = 0;
    reg [1:0]  byte_cnt      = 0;
    reg [11:0] load_addr     = 0;
    reg        we_uart       = 0;
    assign uart_tx = 1'b1;

    reg prev_reset = 0;

    always @(posedge uart_clk) begin
        prev_reset <= reset;
        we_uart <= 0;

        if (reset && !prev_reset) begin
            byte_cnt <= 0;
        end else if (rx_valid) begin
            assemble_word <= {rx_byte, assemble_word[31:8]};
            byte_cnt <= byte_cnt + 1;

            if (byte_cnt == 2'd3) begin
                we_uart <= 1;
                byte_cnt <= 0;
            end
        end
    end

    //--------------------------------------------------
    // PORT B: UART WRITE PORT (clk_uart)
    //--------------------------------------------------
    always @(posedge uart_clk) begin
        if (reset && !prev_reset) begin
            load_addr <= 0;
        end else if (we_uart) begin
            mem[load_addr] <= assemble_word;
            load_addr <= load_addr + 1;
        end
    end

endmodule