// ===================================================================
// mac_s5_10_comb.sv
// 完全組合邏輯：S5.10 × S5.10 → S10.20 → 累加 S10.20
// ===================================================================

// ===================================================================
// mac_s5_10_pipe2.sv
// 2-cycle pipelined MAC: S5.10 × S5.10 → S10.20 → accumulate
// Cycle 1: DSP multiply
// Cycle 2: accumulator add
// ===================================================================

module mac_s5_10 #(
    parameter int FRAC_BITS = 10
)(
    input  logic clk,
    input  logic signed [15:0] in_val,    // S5.10
    input  logic signed [15:0] weight,    // S5.10
    input  logic signed [31:0] acc_in,    // S10.20
    output logic signed [31:0] acc_out    // S10.20
);

    // ----------------------------
    // Stage 1: Multiply
    // ----------------------------
    logic signed [31:0] mult;
    logic signed [31:0] mult_reg;

    assign mult = in_val * weight;   

    always_ff @(posedge clk) begin
        mult_reg <= mult;           
    end

    // ----------------------------
    // Stage 2: Add
    // ----------------------------
    always_ff @(posedge clk) begin
        acc_out <= acc_in + mult_reg;
    end

endmodule

