module mask_argmax (
    // 10-logit output from MLP (S5.10)
    input  logic signed [15:0] act_in [0:9],

    // S5.10 encoded state
    input  logic signed [15:0] live_left,
    input  logic signed [15:0] blank_left,
    input  logic signed [15:0] current_index, 
    input  logic signed [15:0] saw_active,    
    input  logic signed [15:0] reverse_active,
    input  logic signed [15:0] phase_item,
    input  logic signed [15:0] phase_shoot,
    input  logic signed [15:0] player_hp,

    input  logic signed [15:0] magnifier_cnt,
    input  logic signed [15:0] cigarette_cnt,
    input  logic signed [15:0] beer_cnt,
    input  logic signed [15:0] saw_cnt,
    input  logic signed [15:0] handcuff_cnt,
    input  logic signed [15:0] phone_cnt,
    input  logic signed [15:0] reverse_cnt,
    input  logic signed [15:0] opponent_handcuffed,

    // Knowledge Vector (Indices 25-32)
    input  logic signed [15:0] knowledge_0,
    input  logic signed [15:0] knowledge_1,
    input  logic signed [15:0] knowledge_2,
    input  logic signed [15:0] knowledge_3,
    input  logic signed [15:0] knowledge_4,
    input  logic signed [15:0] knowledge_5,
    input  logic signed [15:0] knowledge_6,
    input  logic signed [15:0] knowledge_7,

    input  logic inference_done,
    output logic [3:0] action
);
    
    // ============================================================
    // Decode S5.10 → integer
    // ============================================================
    logic signed [15:0] live_left_i;
    logic signed [15:0] blank_left_i;
    logic signed [15:0] current_idx_i;
    logic signed [15:0] saw_active_i;
    logic signed [15:0] reverse_active_i;

    logic signed [15:0] phase_item_i;
    logic signed [15:0] phase_shoot_i;
    logic signed [15:0] player_hp_i;

    logic signed [15:0] magnifier_i;
    logic signed [15:0] cigarette_i;
    logic signed [15:0] beer_i;
    logic signed [15:0] saw_i;
    logic signed [15:0] handcuff_i;
    logic signed [15:0] phone_i;
    logic signed [15:0] reverse_i;
    logic signed [15:0] opponent_handcuffed_i;

    // Knowledge Selection
    logic signed [15:0] knowledge_val;
    logic signed [15:0] knowledge_val_i;
    logic signed [15:0] effective_knowledge;

    logic [9:0] action_mask;

    assign live_left_i    = live_left    >>> 10;
    assign blank_left_i   = blank_left   >>> 10;
    assign current_idx_i  = current_index >>> 10;
    assign saw_active_i   = saw_active   >>> 10;
    assign reverse_active_i = reverse_active >>> 10;

    assign phase_item_i   = phase_item   >>> 10;
    assign phase_shoot_i  = phase_shoot  >>> 10;
    assign player_hp_i    = player_hp    >>> 10;

    assign magnifier_i    = magnifier_cnt  >>> 10;
    assign cigarette_i    = cigarette_cnt  >>> 10;
    assign beer_i         = beer_cnt       >>> 10;
    assign saw_i          = saw_cnt        >>> 10;
    assign handcuff_i     = handcuff_cnt   >>> 10;
    assign phone_i        = phone_cnt      >>> 10;
    assign reverse_i      = reverse_cnt    >>> 10;
    assign opponent_handcuffed_i = opponent_handcuffed >>> 10;

    // Select the knowledge for the *current* bullet
    always_comb begin
        case (current_idx_i[2:0])
            3'd0: knowledge_val = knowledge_0;
            3'd1: knowledge_val = knowledge_1;
            3'd2: knowledge_val = knowledge_2;
            3'd3: knowledge_val = knowledge_3;
            3'd4: knowledge_val = knowledge_4;
            3'd5: knowledge_val = knowledge_5;
            3'd6: knowledge_val = knowledge_6;
            3'd7: knowledge_val = knowledge_7;
            default: knowledge_val = 16'd0;
        endcase
    end
    assign knowledge_val_i = knowledge_val >>> 10;


    // ============================================================
    // Generate action mask (pure combinational)
    // ============================================================
    always_comb begin
        action_mask = 10'b0;
        effective_knowledge = knowledge_val_i; // Default assignment to prevent latch

        if (phase_item_i == 1) begin
            action_mask[2] = (magnifier_i  > 0 && (knowledge_val_i != 2 && knowledge_val_i != 3));
            action_mask[3] = (cigarette_i  > 0 && player_hp_i < 4);
            action_mask[4] = (beer_i       > 0 && saw_active_i == 0 && (knowledge_val_i != 2 && knowledge_val_i != 3));
            action_mask[5] = (saw_i        > 0 && saw_active_i == 0);
            action_mask[6] = (handcuff_i   > 0 && opponent_handcuffed_i == 0 && (live_left_i + blank_left_i > 1));
            action_mask[7] = (phone_i      > 0);
            action_mask[8] = (reverse_i    > 0 && reverse_active_i == 0 && (knowledge_val_i != 2 && knowledge_val_i != 3));
            action_mask[9] = 1;
        end

        else if (phase_shoot_i == 1) begin
            // Default: Both allowed
            action_mask[0] = 1; // Shoot Enemy
            action_mask[1] = 1; // Shoot Self

            // Rule 1: All remaining are Blank -> Must Shoot Self (unless Reverse is active)
            if (live_left_i == 0 && blank_left_i > 0) begin
                if (reverse_active_i == 1) begin
                    // Effective: All Live -> Shoot Enemy
                    action_mask[0] = 1;
                    action_mask[1] = 0;
                end else begin
                    // Effective: All Blank -> Shoot Self
                    action_mask[0] = 0;
                    action_mask[1] = 1;
                end
            end
            // Rule 2: All remaining are Live -> Must Shoot Enemy (unless Reverse is active)
            else if (live_left_i > 0 && blank_left_i == 0) begin
                if (reverse_active_i == 1) begin
                    // Effective: All Blank -> Shoot Self
                    action_mask[0] = 0;
                    action_mask[1] = 1;
                end else begin
                    // Effective: All Live -> Shoot Enemy
                    action_mask[0] = 1;
                    action_mask[1] = 0;
                end
            end
            
            // Rule 3: Known Next Bullet (1: Unknown, 2: Live, 3: Blank)
            // Handle Reverse Logic: If reverse is active, swap Live/Blank meaning
            effective_knowledge = knowledge_val_i;
            if (reverse_active_i == 1) begin
                if (knowledge_val_i == 2) effective_knowledge = 3;      // Live -> Blank
                else if (knowledge_val_i == 3) effective_knowledge = 2; // Blank -> Live
            end

            // 2: Live (Effective) -> Shoot Enemy (Action 0)
            if (effective_knowledge == 2) begin
                action_mask[0] = 1; // Allow Shoot Enemy
                action_mask[1] = 0; // Block Shoot Self
            end
            // 3: Blank (Effective) -> Shoot Self (Action 1)
            else if (effective_knowledge == 3) begin
                action_mask[0] = 0; // Block Shoot Enemy
                action_mask[1] = 1; // Allow Shoot Self
            end

            // Rule 4: If Saw is active, never Shoot Self (suicide or waste)
            if (saw_active_i == 1) begin
                action_mask[1] = 0;
                if (action_mask[0] == 0) action_mask[0] = 1; // Prevent deadlock
            end
        end
    end


    // ============================================================
    // Masked logits
    // ============================================================
    logic signed [15:0] masked [0:9];

    always_comb begin
        for (int i = 0; i < 10; i++)
            masked[i] = (action_mask[i] ? act_in[i] : -16'sd32768);
    end


    // ============================================================
    // Argmax (pure combinational)
    // ============================================================
    logic signed [15:0] best_val;
    logic [3:0] best_idx;

    always_comb begin
        best_val = masked[0];
        best_idx = 4'd0;

        for (int i = 0; i < 10; i++) begin
            if (masked[i] > best_val) begin
                best_val = masked[i];
                best_idx = i[3:0];
            end
        end
    end

    assign action = (inference_done)? best_idx:4'd15 ;

endmodule


