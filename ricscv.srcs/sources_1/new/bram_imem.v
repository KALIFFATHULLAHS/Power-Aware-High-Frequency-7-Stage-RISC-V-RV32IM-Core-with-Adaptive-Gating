module bram_imem(
    input  wire        clk,          // CPU clock
    input  wire [13:0] addr,
    output reg  [31:0] rdata,

    input  wire        uart_clk,     // UART clock
    input  wire        uart_rx,
    output wire        uart_tx       // not used here but kept if needed
);

    // 4K words (16KB)
    (* ram_style = "block" *) reg [31:0] mem [0:4095];

    initial begin
        $readmemh("program.mem", mem);
        $display("[BRAM] Memory loaded with 'program.mem' successfully.");
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
    .CLK_FREQ(100_000_000),
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

    always @(posedge uart_clk) begin
        we_uart <= 0;

        if (rx_valid) begin
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
        if (we_uart) begin
            mem[load_addr] <= assemble_word;
            load_addr <= load_addr + 1;
        end
    end

endmodule