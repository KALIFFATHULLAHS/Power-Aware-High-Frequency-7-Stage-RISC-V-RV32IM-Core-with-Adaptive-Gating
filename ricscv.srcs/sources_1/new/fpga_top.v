`timescale 1ns/1ps

module fpga_top (
    input  wire        clk_in,
    input  wire        reset,   // press = reset=1
    input  wire        uart_rx,
    output wire        uart_tx,
    output wire [7:0] led
);

    wire bt_reset = reset;

    wire dbg_wfi_active;
    wire [7:0] dbg_led;

    riscv_core_top core (
        .clk_in        (clk_in),
        .reset         (bt_reset),
        .uart_rx       (uart_rx),
        .uart_tx       (uart_tx),
        .dbg_wfi_active(dbg_wfi_active),
        .dbg_led       (dbg_led)
        // if you add .dbg_led(dbg_led) later, we'll hook it here
    );

    // Simple LED debug for now: show reset + WFI
     assign led = dbg_led;
endmodule
