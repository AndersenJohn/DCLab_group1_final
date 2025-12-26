module RL_model #(
    parameter int IN_DIM    = 33,
    parameter int H1_DIM    = 128,
    parameter int H2_DIM    = 128,
    parameter int OUT_DIM   = 10,
    parameter int P         = 16,
    parameter int FRAC_BITS = 10
)(
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic signed [15:0] in_vec  [0:IN_DIM-1],

    output logic signed [15:0] H1_vec [0:H1_DIM-1],
    output logic signed [15:0] H2_vec [0:H2_DIM-1],
    output logic signed [15:0] out_vec [0:OUT_DIM-1],

    output logic [3:0]  action
    
);

    //----------------------------------------------------------------
    // Internal signals
    //----------------------------------------------------------------
    logic done;

    //----------------------------------------------------------------
    // MLP inference
    //----------------------------------------------------------------
    mlp_inference #(
        .IN_DIM(IN_DIM),
        .H1_DIM(H1_DIM),
        .H2_DIM(H2_DIM),
        .OUT_DIM(OUT_DIM),
        .P(P),
        .FRAC_BITS(FRAC_BITS)
    ) u_mlp (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .done(done),
        .in_vec(in_vec),
        .H1_vec(H1_vec),
        .H2_vec(H2_vec),
        .out_vec(out_vec)
    );
    //----------------------------------------------------------------
    // Mask + Argmax module
    //----------------------------------------------------------------
    mask_argmax u_mask (
        .act_in(out_vec),

        // Extract RL state from input vector
        .live_left     (in_vec[0]),
        .blank_left    (in_vec[1]),
        .current_index (in_vec[2]),
        .saw_active    (in_vec[3]),
        .reverse_active(in_vec[4]),
        .phase_item    (in_vec[5]),
        .phase_shoot   (in_vec[6]),
        .player_hp     (in_vec[7]),
        .magnifier_cnt (in_vec[9]),
        .cigarette_cnt (in_vec[10]),
        .beer_cnt      (in_vec[11]),
        .saw_cnt       (in_vec[12]),
        .handcuff_cnt  (in_vec[13]),
        .phone_cnt     (in_vec[14]),
        .reverse_cnt   (in_vec[15]),
        .opponent_handcuffed (in_vec[17]),
        
        // Knowledge Vector (Indices 25-32)
        .knowledge_0   (in_vec[25]),
        .knowledge_1   (in_vec[26]),
        .knowledge_2   (in_vec[27]),
        .knowledge_3   (in_vec[28]),
        .knowledge_4   (in_vec[29]),
        .knowledge_5   (in_vec[30]),
        .knowledge_6   (in_vec[31]),
        .knowledge_7   (in_vec[32]),

        .inference_done(done),

        .action(action)
    );

endmodule

