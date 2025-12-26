module mlp_inference #(
    parameter int IN_DIM   = 33,
    parameter int H1_DIM   = 128,
    parameter int H2_DIM   = 128,
    parameter int OUT_DIM  = 10,
    parameter int P        = 16,
    parameter int FRAC_BITS = 10
) (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    output logic done,
    input  logic signed [15:0] in_vec  [0:IN_DIM-1],
    output logic signed [15:0] H1_vec [0:H1_DIM-1],
    output logic signed [15:0] H2_vec [0:H2_DIM-1],
    output logic signed [15:0] out_vec [0:OUT_DIM-1]
);

    logic signed [15:0] act1 [0:H1_DIM-1];
    logic signed [15:0] act2 [0:H2_DIM-1];
    logic signed [15:0] act3 [0:OUT_DIM-1];


    logic start1, start2, start3;
    logic done1, done2, done3;

    // --------------------------------------------------------
    // Layer 1 Instantiation 
    // FC1: 33 -> 128, ReLU = 1
    // --------------------------------------------------------
    fc1_layer_parallel #(
        .IN_DIM(IN_DIM), 
        .OUT_DIM(H1_DIM), 
        .P(P), 
        .FRAC_BITS(FRAC_BITS), 
        .HAS_RELU(1'b1)
    ) fc1 (
        .clk(clk),
        .rst_n(rst_n),
        .start(start1),
        .done(done1),
        .act_in(in_vec),
        .act_out(act1)
    );

    // --------------------------------------------------------
    // Layer 2 Instantiation 
    // FC2: 128 -> 128, ReLU = 1
    // --------------------------------------------------------
    fc2_layer_parallel #(
        .IN_DIM(H1_DIM), 
        .OUT_DIM(H2_DIM), 
        .P(P), 
        .FRAC_BITS(FRAC_BITS), 
        .HAS_RELU(1'b1)
    ) fc2 (
        .clk(clk),
        .rst_n(rst_n),
        .start(start2),
        .done(done2),
        .act_in(act1),
        .act_out(act2)
    );

    // --------------------------------------------------------
    // Layer 3 Instantiation 
    // FC3: 128 -> 10, ReLU = 0
    // --------------------------------------------------------
    fc3_layer_parallel #(
        .IN_DIM(H2_DIM), 
        .OUT_DIM(OUT_DIM), 
        .P(P), 
        .FRAC_BITS(FRAC_BITS), 
        .HAS_RELU(1'b0)
    ) fc3 (
        .clk(clk),
        .rst_n(rst_n),
        .start(start3),
        .done(done3),
        .act_in(act2),
        .act_out(act3)
    );

    genvar i;
    generate
        for (i = 0; i < H1_DIM; i=i+1) begin : H1_ASSIGN
            assign H1_vec[i] = act1[i];
        end
    endgenerate

    generate
        for (i = 0; i < H2_DIM; i=i+1) begin : H2_ASSIGN
            assign H2_vec[i] = act2[i];
        end
    endgenerate


    generate
        for (i = 0; i < OUT_DIM; i=i+1) begin : OUT_ASSIGN
            assign out_vec[i] = act3[i];
        end
    endgenerate


   
    

    localparam S_IDLE  = 2'd0;
    localparam S_RUN1  = 2'd1;
    localparam S_RUN2  = 2'd2;
    localparam S_RUN3  = 2'd3;
    logic [1:0] state_r, state_w;

    always_comb begin
        state_w = state_r;
        start1  = 1'b0; start2 = 1'b0; start3 = 1'b0;
        done    = 1'b0;
        case (state_r)
            S_IDLE:  if (start) begin start1 = 1'b1; state_w = S_RUN1; end
            S_RUN1:  if (done1) begin start2 = 1'b1; state_w = S_RUN2; end
            S_RUN2:  if (done2) begin start3 = 1'b1; state_w = S_RUN3; end
            S_RUN3:  if (done3) begin done = 1'b1; state_w = S_IDLE; end
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) state_r <= S_IDLE;
        else        state_r <= state_w;
    end

endmodule
