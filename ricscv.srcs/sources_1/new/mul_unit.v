module mul_unit (
    input  wire        clk,
    input  wire        reset,
    input  wire        start,
    input  wire [2:0]  op_type,          // funct3: 000:mul, 001:mulh, 010:mulhsu, 011:mulhu
    input  wire [31:0] op_a,
    input  wire [31:0] op_b,

    output reg [31:0]  result,
    output reg         busy
);

    reg [63:0] product;
    
    // Signed extensions
    wire [63:0] product_ss = $signed(op_a) * $signed(op_b);
    wire [63:0] product_su = $signed(op_a) * $signed({1'b0, op_b});
    wire [63:0] product_uu = op_a * op_b;

    always @(posedge clk) begin
        if (reset) begin
            busy   <= 0;
            result <= 0;
        end
        else if (start) begin
            case (op_type)
                3'b000: result <= product_uu[31:0];   // MUL
                3'b001: result <= product_ss[63:32];  // MULH
                3'b010: result <= product_su[63:32];  // MULHSU
                3'b011: result <= product_uu[63:32];  // MULHU
                default: result <= 0;
            endcase
            busy <= 0;
        end
    end

endmodule

