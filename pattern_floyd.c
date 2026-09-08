// =====================================================================
// RISC-V RV32IM C SOURCE CODE: FLOYD'S TRIANGLE PATTERN (N = 5)
// Target Output:
// 1
// 2 3
// 4 5 6
// 7 8 9 10
// 11 12 13 14 15
// =====================================================================

#define MMIO_UART_TX (*((volatile unsigned int *)0xFFFF0000))
#define MMIO_LED_OUT (*((volatile unsigned int *)0xFFFF0004))

void uart_putchar(char c) {
    MMIO_UART_TX = (unsigned int)c;
}

void print_number(int num) {
    if (num >= 10) {
        uart_putchar('0' + (num / 10));
        uart_putchar('0' + (num % 10));
    } else {
        uart_putchar('0' + num);
    }
}

int main() {
    int num = 1;
    int n = 5;

    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= i; j++) {
            print_number(num);
            num++;
            if (j < i) {
                uart_putchar(' ');
            }
        }
        uart_putchar('\r');
        uart_putchar('\n');
    }

    MMIO_LED_OUT = num; // Output final counter to hardware LEDs

    // Wait For Interrupt (WFI) Low-Power Shutdown
    __asm__ volatile ("wfi");

    return 0;
}
