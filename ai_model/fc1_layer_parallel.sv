// ============================================================
// fc_layer_parallel.sv
// Fully-connected layer with P MACs, S5.10 precision
// Uses On-Chip Memory IPs for Weights and Biases
// ============================================================
module fc1_layer_parallel #(
    parameter int IN_DIM    = 33,
    parameter int OUT_DIM   = 128,
    parameter int P         = 16,
    parameter int FRAC_BITS = 10,
    parameter int HAS_RELU  = 1'b1
) (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    output logic done,
    input  logic signed [15:0] act_in  [0:IN_DIM-1],
    output logic signed [15:0] act_out [0:OUT_DIM-1]
);

    // --------------------------------------------------------
    // FSM 狀態定義
    // --------------------------------------------------------
    typedef enum logic [2:0] {
        S_IDLE      = 3'd0,
        S_WAIT_BIAS = 3'd1, 
        S_LOAD_BIAS = 3'd2, 
        S_MAC_LOOP0 = 3'd3, 
        S_MAC_LOOP1 = 3'd4, 
        S_MAC_LOOP2 = 3'd5, 
        S_MAC_LOOP3 = 3'd6, 
        S_WRITE_OUT = 3'd7
    } state_t;

    state_t state_r, state_w;
    localparam int GROUPS = (OUT_DIM + P - 1) / P;

    logic [$clog2(P)      -1:0] local_idx_r, local_idx_w;  // 0 ~ P-1
    logic [$clog2(GROUPS) -1:0] group_idx_r, group_idx_w;  // 0 ~ GROUPS-1
    logic [$clog2(IN_DIM) -1:0] in_idx_r,    in_idx_w;     // 0 ~ IN_DIM-1

    // --------------------------------------------------------
    // Bias BRAM 
    // --------------------------------------------------------
    // Depth=8 (128/16), Address width = 3
    logic [2:0]   bias_addr; 
    logic [255:0] bias_rom_q;
    logic signed [15:0] bias_bus [0:P-1];

    // IP : Bias
    fc1_bias fc1_bias_inst (
        .address ( bias_addr ),
        .clock   ( clk ),
        .q       ( bias_rom_q )
    );
    
    // Bias Address 
    assign bias_addr = group_idx_r[2:0];

    genvar k;
    // Bias bus (LSB First: q[15:0] -> MAC0)
    generate
        for (k = 0; k < P; k=k+1) begin : BIAS_SLICE
            assign bias_bus[k] = bias_rom_q[(k*16) +: 16];
        end
    endgenerate

    // --------------------------------------------------------
    // Weight BRAM 
    // --------------------------------------------------------
    // Depth=264, Address width = 9
    logic [8:0]   rom_addr; 
    logic [255:0] rom_q;    // Weight BRAM 輸出
    logic signed [15:0] w_bus [0:P-1];

    // IP 實例化: Weight
    fc1_weight fc1_weight_inst (
        .address ( rom_addr ),
        .clock   ( clk ),
        .q       ( rom_q )
    );

    // Weight Address 
    assign rom_addr = (group_idx_r * IN_DIM) + in_idx_r;

    // Weight bus (LSB First: q[15:0] -> MAC0)
    generate
        for (k = 0; k < P; k=k+1) begin : WEIGHT_SLICE
            assign w_bus[k] = rom_q[(k*16) +: 16]; 
        end
    endgenerate

    // --------------------------------------------------------
    // MAC 陣列
    // --------------------------------------------------------
    logic signed [31:0] psum_r [0:P-1];
    logic signed [31:0] psum_w [0:P-1];
    logic signed [15:0] act_in_broadcast;

    // Mac array instantiation
    generate
        for (k = 0; k < P; k=k+1) begin : MAC_ARRAY
            mac_s5_10 #(.FRAC_BITS(FRAC_BITS)) mac_inst (
                .clk(clk),
                .in_val (act_in_broadcast),
                .weight (w_bus[k]),
                .acc_in (psum_r[k]),
                .acc_out(psum_w[k])
            );
        end
    endgenerate

    // --------------------------------------------------------
    // Output Buffer & Done Signal
    // --------------------------------------------------------
    logic signed [15:0] act_out_r [0:OUT_DIM-1];
    logic signed [15:0] act_out_w [0:OUT_DIM-1];
    logic               done_r, done_w;

    assign act_out = act_out_r;
    assign done    = done_r;

    // --------------------------------------------------------
    // temp
    // --------------------------------------------------------
    logic [$clog2(OUT_DIM)-1:0] out_idx;
    logic signed [31:0]         acc, shifted;

    assign out_idx          = group_idx_r * P + local_idx_r;
    assign act_in_broadcast = act_in[in_idx_r];
    assign acc              = psum_r[local_idx_r];
    assign shifted          = $signed(acc) >>> FRAC_BITS;

    // --------------------------------------------------------
    // FSM Next-State Logic
    // --------------------------------------------------------
    always_comb begin
        // default assignments
        state_w     = state_r;
        local_idx_w = local_idx_r;
        group_idx_w = group_idx_r;
        in_idx_w    = in_idx_r;
        done_w      = done_r;
        act_out_w   = act_out_r;

        case (state_r)

            S_IDLE: begin
                done_w      = 1'b0;
                if (start) begin
                    local_idx_w = '0;
                    group_idx_w = '0; // Reset Group -> Bias Addr = 0
                    in_idx_w    = '0;
                    state_w     = S_WAIT_BIAS; //wait  Bias data
                end
            end

            S_WAIT_BIAS: begin
                state_w = S_LOAD_BIAS;
            end

            S_LOAD_BIAS: begin
                if (local_idx_r == P-1) begin
                    local_idx_w = '0;
                    state_w     = S_MAC_LOOP0; 
                end else begin
                    local_idx_w = local_idx_r + 1;
                end
            end

            S_MAC_LOOP0: begin
                state_w = S_MAC_LOOP1;
            end


            S_MAC_LOOP1: begin
                state_w = S_MAC_LOOP2;
            end
            

            S_MAC_LOOP2: begin
                state_w = S_MAC_LOOP3;
            end


            S_MAC_LOOP3: begin
                if (in_idx_r < IN_DIM - 1) begin
                    in_idx_w = in_idx_r + 1;
                    state_w = S_MAC_LOOP0; 
                end else begin
                    in_idx_w    = '0;
                    local_idx_w = '0;
                    state_w     = S_WRITE_OUT; 
                end
            end

            S_WRITE_OUT: begin
                if (out_idx < OUT_DIM) begin
                    if (HAS_RELU && shifted[31])
                        act_out_w[out_idx] = 16'sd0;
                    else
                        act_out_w[out_idx] = shifted[15:0];
                end

                // 2. 切換邏輯
                if (local_idx_r == P - 1) begin
                    local_idx_w = '0;
                    if (group_idx_r == GROUPS - 1) begin
                        done_w  = 1'b1;
                        state_w = S_IDLE;
                    end else begin
                        group_idx_w = group_idx_r + 1; 
                        state_w     = S_WAIT_BIAS;
                    end
                end else begin
                    local_idx_w = local_idx_r + 1;
                end
            end

        endcase
    end

    // --------------------------------------------------------
    // Sequential Logic (Register Update)
    // --------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_r     <= S_IDLE;
            local_idx_r <= '0;
            group_idx_r <= '0;
            in_idx_r    <= '0;
            done_r      <= 1'b0;
            for (int i = 0; i < P; i++)      psum_r[i]  <= '0;
            for (int j = 0; j < OUT_DIM; j++) act_out_r[j] <= '0;
        end else begin
            state_r     <= state_w;
            local_idx_r <= local_idx_w;
            group_idx_r <= group_idx_w;
            in_idx_r    <= in_idx_w;
            done_r      <= done_w;

            // psum_r 更新邏輯
            for (int i = 0; i < P; i++) begin

                // ------- 1. 載入 bias -------
                if (state_r == S_LOAD_BIAS && local_idx_r == i) begin
                    if (out_idx < OUT_DIM)
                        psum_r[i] <= {{(32-16){bias_bus[i][15]}}, bias_bus[i]} <<< FRAC_BITS;
                    else
                        psum_r[i] <= '0;
                end

                // ------- 2. MAC 運算結果寫入 -------
                else if (state_r == S_MAC_LOOP3) begin
                    psum_r[i] <= psum_w[i];
                end

                // ------- 3. 保持數值 -------
                else begin
                    psum_r[i] <= psum_r[i]; 
                end
            end

            for (int j = 0; j < OUT_DIM; j++)
                act_out_r[j] <= act_out_w[j];
        end
    end

endmodule
