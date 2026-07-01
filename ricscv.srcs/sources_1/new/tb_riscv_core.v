`timescale 1ns/1ps

module tb_riscv_core;

    // ======================================================
    // CLOCK + RESET
    // ======================================================
    reg clk_in = 0;
    always #5 clk_in = ~clk_in;      // 100 MHz

    reg reset = 1;

    // UART idle lines
    reg  uart_rx = 1;
    wire uart_tx;

    wire dbg_wfi_active;

    // ======================================================
    // RESET SEQUENCE
    // ======================================================
   initial begin
    reset = 1;
    uart_rx = 1;
    #200;
    reset = 0;
end


    // ======================================================
    // DUT INSTANTIATION
    // ======================================================
    riscv_core_top dut (
        .clk_in       (clk_in),
        .reset        (reset),

        .uart_rx      (uart_rx),
        .uart_tx      (uart_tx),

        .dbg_wfi_active (dbg_wfi_active)
    );

    // ======================================================
    // STOP SIM AFTER SOME TIME
    // ======================================================
    initial begin
        #100000;        // 100 us of simulation time
        $finish;
    end

endmodule
