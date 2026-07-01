`timescale 1ns/1ps

module riscv_core_tb;

    // Parameters
    parameter CLK_PERIOD = 10; // 100MHz

    // Signals
    reg        clk_in;
    reg        reset;
    reg        uart_rx;
    wire       uart_tx;
    wire       dbg_wfi_active;
    wire [7:0] dbg_led;

    // Instantiate Top Module
    riscv_core_top dut (
        .clk_in(clk_in),
        .reset(reset),
        .uart_rx(uart_rx),
        .uart_tx(uart_tx),
        .dbg_wfi_active(dbg_wfi_active),
        .dbg_led(dbg_led)
    );

    // Clock Generation
    initial begin
        clk_in = 0;
        forever #(CLK_PERIOD/2) clk_in = ~clk_in;
    end

    // UART monitor logic (approximate bit sampling)
    // 115200 baud at 100MHz is ~868 cycles per bit
    integer bit_period = 8680; // 868 * 10ns
    reg [7:0] rx_byte;
    integer i;
    always @(negedge uart_tx) begin
        // Start bit detected
        #(bit_period / 2); // mid-point of start bit
        #(bit_period);     // mid-point of bit 0
        
        for (i=0; i<8; i=i+1) begin
            rx_byte[i] = uart_tx;
            #(bit_period);
        end
        
        $display("[UART] Received Byte: %d (0x%h) at time %t", rx_byte, rx_byte, $time);
    end

    // Simulation Flow
    initial begin
        reset = 1;
        uart_rx = 1;
        
        $display("--- Starting RISC-V 7-Stage Simulation ---");
        #(CLK_PERIOD * 20);
        reset = 0;
        
        $display("--- Reset Released. Processor Fetching... ---");
        
        // Let it run for a while to complete calculations
        // Each instruction (~55 instructions in total path + stalls)
        #(CLK_PERIOD * 50000); 
        
        $display("--- Simulation Finished ---");
        $finish;
    end

    // Monitor internal registers for curiosity (Optional - depends on internal signal names)
    // initial begin
    //    $monitor("Time: %t | PC: %h | Register x3: %h", $time, dut.if1_pc, dut.rf.regs[3]);
    // end

endmodule
