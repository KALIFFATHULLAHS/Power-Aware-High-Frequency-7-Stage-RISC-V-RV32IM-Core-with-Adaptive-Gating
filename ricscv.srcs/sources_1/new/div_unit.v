module div_unit (
    input  wire        clk,
    input  wire        reset,
    input  wire        start,
    input  wire [2:0]  op_type,          // funct3: 100:div, 101:divu, 110:rem, 111:remu
    input  wire [31:0] op_a,
    input  wire [31:0] op_b,

    output reg [31:0]  result,
    output reg         busy
);

    reg [5:0]  count;
    reg [63:0] dividend;
    reg [31:0] divisor;
    reg        neg_q, neg_r;

    wire is_div_s = (op_type == 3'b100);
    wire is_rem_s = (op_type == 3'b110);

    always @(posedge clk) begin
        if (reset) begin
            busy <= 0;
            count <= 0;
            result <= 0;
        end
        else if (start && !busy) begin
            busy <= 1;
            count <= 32;
            
            // Handle signs for signed ops
            if ((is_div_s || is_rem_s) && op_a[31]) begin
                dividend <= {32'b0, -op_a};
                neg_r <= 1'b1;
            end else begin
                dividend <= {32'b0, op_a};
                neg_r <= 1'b0;
            end

            if ((is_div_s || is_rem_s) && op_b[31]) begin
                divisor <= -op_b;
                neg_q <= (is_div_s) ? !op_a[31] : 1'b0; // neg_q = rs1^rs2 for div
            end else begin
                divisor <= op_b;
                neg_q <= (is_div_s) ? op_a[31] : 1'b0;
            end
            
            if (is_div_s) neg_q <= op_a[31] ^ op_b[31];
            if (is_rem_s) neg_r <= op_a[31];
        end
        else if (busy) begin
            if (count != 0) begin
                if (dividend[62:31] >= divisor) begin
                    dividend <= { (dividend[62:31] - divisor), dividend[30:0], 1'b1 };
                end else begin
                    dividend <= { dividend[62:0], 1'b0 };
                end
                count <= count - 1;
            end else begin
                case (op_type)
                    3'b100, 3'b101: result <= neg_q ? -dividend[31:0] : dividend[31:0]; // DIV/DIVU
                    3'b110, 3'b111: result <= neg_r ? -dividend[63:32] : dividend[63:32]; // REM/REMU
                    default: result <= 0;
                endcase
                busy <= 0;
            end
        end
    end

endmodule

